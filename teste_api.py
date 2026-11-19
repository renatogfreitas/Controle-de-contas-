#!/usr/bin/env python3
"""
Teste SOMENTE LEITURA da API do Controle Odonto (Aplicativo.NET).

Como usar (no terminal do seu computador):
    export CO_USER="seu_usuario"
    export CO_PASS="sua_senha"
    python3 teste_api.py            # gera RELATORIO_TESTE_API.md

Garantias:
  * usuário e senha são lidos só das variáveis de ambiente (nunca gravados);
  * o token só aparece com os 10 primeiros caracteres;
  * nomes, telefones, CPF, e-mail etc. são mascarados antes de aparecer na
    tela ou no relatório;
  * só faz consultas (GET) + login e renovação de token (POST). Nada é alterado.

Só usa a biblioteca padrão do Python 3 (nada para instalar).
"""
import calendar
import collections
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, timedelta

BASE = os.environ.get("CO_BASE_URL", "https://api.aplicativo.net").rstrip("/")
PACE = 0.6  # segundos entre chamadas (aumenta sozinho se houver 429)

# ----------------------------------------------------------------------------
# Mascaramento (LGPD)
# ----------------------------------------------------------------------------
PHONE_KEY = re.compile(r"(telefone|celular|fone|whats|^tel)", re.I)
HIDE_KEY = re.compile(
    r"(cpf|cnpj|e_?mail|^rg$|documento|nascimento|endereco|logradouro|cep|"
    r"bairro|complemento|observ|^obs|descri|historico|anotac|mensagem)", re.I)
NAME_KEY = re.compile(r"(nome|paciente|pessoa|cliente|responsavel|devedor|sacado)", re.I)
SAFE_KEY = re.compile(
    r"(especie|forma_?pagamento|situacao|status|tipo|plano|procedimento|"
    r"convenio|categoria|banco)", re.I)
TOKEN_KEY = re.compile(r"token", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
SKIP_WORDS = {"da", "de", "do", "das", "dos", "e"}


def mask_name(v):
    words = [w for w in re.findall(r"[^\W\d_]+", str(v), re.U) if w.lower() not in SKIP_WORDS]
    return "".join(w[0].upper() + "." for w in words) or "[vazio]"


def mask_phone(v):
    d = re.sub(r"\D", "", str(v))
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if len(d) >= 10:
        local = d[-9:] if len(d) >= 11 else d[-8:]
        ddd = d[-11:-9] if len(d) >= 11 else d[-10:-8]
        return "(%s) %s****-**%s" % (ddd, local[0], d[-2:])
    return "(sem DDD) ****-**%s" % d[-2:] if len(d) >= 2 else "[vazio]"


def mask(obj, key=""):
    """Devolve uma cópia de `obj` com dados pessoais mascarados."""
    if isinstance(obj, dict):
        if HIDE_KEY.search(key) and key:
            return "[oculto]"
        return {k: mask(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask(x, key) for x in obj]
    if obj is None or obj == "":
        return obj
    if key and HIDE_KEY.search(key):
        return "[oculto]"
    if key and TOKEN_KEY.search(key) and isinstance(obj, str):
        return obj[:10] + "…"
    if key and PHONE_KEY.search(key):
        return mask_phone(obj)
    if isinstance(obj, str):
        if EMAIL_RE.search(obj) or CPF_RE.search(obj):
            return "[oculto]"
        if key and NAME_KEY.search(key) and not SAFE_KEY.search(key):
            return mask_name(obj)
    return obj


def trim(obj, depth=0):
    """Encurta o exemplo: no máximo 2 itens por lista e textos de 80 caracteres."""
    if isinstance(obj, dict):
        return {k: trim(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [trim(x, depth + 1) for x in obj[:2]]
    if isinstance(obj, str) and len(obj) > 80:
        return obj[:80] + "…"
    return obj


def sanitize_text(text):
    """Última rede de segurança antes de mostrar/gravar qualquer texto."""
    text = EMAIL_RE.sub("[oculto]", text)
    return CPF_RE.sub("[oculto]", text)


def fmt_pattern(v):
    """Formato sem revelar dígitos reais: '(12) 99999-9999' -> '(99) 99999-9999'."""
    return type(v).__name__ + ":" + re.sub(r"\d", "9", str(v))


# ----------------------------------------------------------------------------
# Utilidades de dados
# ----------------------------------------------------------------------------
def parse_num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = re.sub(r"[^\d,.\-]", "", v)
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def parse_date(v):
    if not isinstance(v, str):
        return None
    for pat, f in ((r"^(\d{4})-(\d{2})-(\d{2})", lambda m: (m[0], m[1], m[2])),
                   (r"^(\d{2})/(\d{2})/(\d{4})", lambda m: (m[2], m[1], m[0]))):
        m = re.match(pat, v.strip())
        if m:
            try:
                y, mo, d = (int(x) for x in f(m.groups()))
                return date(y, mo, d)
            except ValueError:
                return None
    return None


def pick_key(rec, exact=(), regex=None):
    low = {k.lower(): k for k in rec}
    for c in exact:
        if c.lower() in low:
            return low[c.lower()]
    if regex:
        for k in rec:
            if re.search(regex, k, re.I):
                return k
    return None


def find_records(obj):
    """Acha a lista principal de registros (lista de dicionários) na resposta."""
    d = obj
    if isinstance(d, dict) and "data" in d:
        d = d["data"]
    if isinstance(d, dict):
        cands = [v for v in d.values() if isinstance(v, list) and v and isinstance(v[0], dict)]
        for v in d.values():  # um nível a mais (ex.: data.lista)
            if isinstance(v, dict):
                cands += [w for w in v.values() if isinstance(w, list) and w and isinstance(w[0], dict)]
        d = max(cands, key=len) if cands else [d]
    if isinstance(d, list):
        dicts = [x for x in d if isinstance(x, dict)]
        if not dicts:
            return []
        if any("id" in x for x in dicts):
            return dicts
        out = []
        for x in dicts:  # agenda agrupada por dia: achata as listas internas
            for v in x.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    out += v
        return out or dicts
    return []


def walk_pairs(o, prefix=""):
    """Todos os pares (chave, valor) de um registro, inclusive aninhados."""
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                yield from walk_pairs(v, k)
            else:
                yield k, v
    elif isinstance(o, list):
        for x in o:
            yield from walk_pairs(x, prefix)


def classify_phone(v):
    d = re.sub(r"\D", "", str(v or ""))
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if not d:
        return "vazio"
    if len(d) == 11 and d[2] == "9":
        return "celular com DDD"
    if len(d) == 10 and d[2] in "2345":
        return "fixo com DDD"
    if len(d) in (8, 9):
        return "sem DDD"
    return "formato estranho"


PHONE_RANK = ["celular com DDD", "fixo com DDD", "sem DDD", "formato estranho", "vazio"]


def phone_summary(records):
    """Resumo agregado (sem números reais) dos campos de telefone."""
    keys = collections.Counter()
    best = collections.Counter()
    formats = collections.Counter()
    for r in records:
        classes = []
        for k, v in walk_pairs(r):
            if PHONE_KEY.search(k):
                keys[k] += 1
                classes.append(classify_phone(v))
                if v not in (None, ""):
                    formats[k + " -> " + fmt_pattern(v)] += 1
        if classes:
            best[min(classes, key=PHONE_RANK.index)] += 1
        else:
            best["sem campo de telefone"] += 1
    return keys, best, formats


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------
class Api:
    def __init__(self):
        self.token = None
        self.refresh_token = None
        self.t_login = 0
        self.pace = PACE
        self.n429 = 0

    def _http(self, method, path, json_body=None, form=None, auth=True):
        headers = {"Accept": "application/json"}
        data = None
        if auth and self.token:
            headers["Authorization"] = "Bearer " + self.token
        if form is not None:
            b = uuid.uuid4().hex
            body = "".join('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (b, k, v)
                           for k, v in form.items()) + "--%s--\r\n" % b
            data = body.encode("utf-8")
            headers["Content-Type"] = "multipart/form-data; boundary=" + b
        elif json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
        t0 = time.monotonic()
        status, raw, retry_after, err = None, b"", None, None
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                status, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, raw, retry_after = e.code, e.read(), e.headers.get("Retry-After")
        except Exception as e:  # rede, DNS, timeout...
            err = type(e).__name__
        ms = int((time.monotonic() - t0) * 1000)
        js = None
        if raw:
            try:
                js = json.loads(raw.decode("utf-8-sig"))
            except ValueError:
                js = None
        detail = None
        if status and status >= 400:
            if isinstance(js, dict):
                for k in ("message", "mensagem", "title", "detail", "error"):
                    if isinstance(js.get(k), str):
                        detail = sanitize_text(js[k])[:120]
                        break
            if not detail and isinstance(js, dict) and isinstance(js.get("messages"), list):
                detail = sanitize_text("; ".join(str(m) for m in js["messages"]))[:120]
            detail = detail or "(sem detalhe)"
        return {"status": status, "ms": ms, "json": js, "error": err,
                "detail": detail, "retry_after": retry_after}

    def request(self, method, path, **kw):
        for attempt in range(4):  # só repete em caso de 429
            res = self._http(method, path, **kw)
            if res["status"] != 429:
                break
            self.n429 += 1
            wait = float(res["retry_after"]) if (res["retry_after"] or "").isdigit() else 10 * (attempt + 1)
            self.pace += 0.5
            print("   429 (limite de chamadas): aguardando %.0fs e reduzindo o ritmo..." % wait)
            time.sleep(wait)
        time.sleep(self.pace)
        return res

    def get(self, path):
        if self.token and time.time() - self.t_login > 25 * 60:  # token vale 30 min
            self.refresh()
        return self.request("GET", path)

    def login(self, user, pwd):
        res = self.request("POST", "/v4/Auth/co", form={"Nome": user, "Senha": pwd}, auth=False)
        d = (res["json"] or {}).get("data") if isinstance(res["json"], dict) else None
        if res["status"] == 200 and isinstance(d, dict) and d.get("accessToken"):
            self.token, self.refresh_token, self.t_login = d["accessToken"], d.get("refreshToken"), time.time()
        return res

    def refresh(self):
        res = self.request("POST", "/v4/Auth/refresh/co",
                           json_body={"token": self.token, "refreshToken": self.refresh_token}, auth=False)
        d = (res["json"] or {}).get("data") if isinstance(res["json"], dict) else None
        if res["status"] == 200 and isinstance(d, dict) and d.get("accessToken"):
            self.token = d["accessToken"]
            self.refresh_token = d.get("refreshToken") or self.refresh_token
            self.t_login = time.time()
        return res


# ----------------------------------------------------------------------------
# Execução dos testes
# ----------------------------------------------------------------------------
class Report:
    def __init__(self):
        self.rows = []      # tabela principal
        self.samples = []   # exemplos mascarados
        self.notes = []     # erros / limites / comportamentos
        self.extra = {}     # seções calculadas

    def add(self, num, name, template, res, records=None, sample=None, note=None):
        st = res["status"]
        ok = st in (200, 204)
        count = "-" if not ok else (0 if st == 204 else (len(records) if records is not None else "-"))
        self.rows.append((num, name, template, st if st else "sem resposta (%s)" % res["error"],
                          ("sim" if ok else "NÃO") + (" (204 = sem dados)" if st == 204 else ""),
                          count, "%d ms" % res["ms"]))
        if sample is not None:
            self.samples.append((num, name, template, sample))
        if not ok:
            self.notes.append("%s %s -> %s %s" % (num, template, st or res["error"], res["detail"] or ""))
        if note:
            self.notes.append("%s: %s" % (num, note))
        print("  [%s] %-38s status=%s  registros=%s  %s" % (num, name, st or res["error"], count, "%d ms" % res["ms"]))


def sample_of(records, js=None):
    if records:
        return trim(mask(records[0]))
    if js is not None:
        return trim(mask(js))
    return None


def month_range(d):
    return d.replace(day=1), d.replace(day=calendar.monthrange(d.year, d.month)[1])


def run(api, est):
    rep = Report()
    today = date.today()
    iso = lambda d: d.isoformat()
    m_ini, m_fim = month_range(today)
    prev_last = m_ini - timedelta(days=1)
    p_ini, p_fim = month_range(prev_last)
    d60 = today - timedelta(days=60)
    yesterday = today - timedelta(days=1)
    E = str(est)

    def fetch(num, name, tpl, path, **kw):
        res = api.get(path)
        recs = find_records(res["json"]) if res["status"] == 200 else ([] if res["status"] == 204 else None)
        rep.add(num, name, tpl, res, recs, sample_of(recs, res["json"] if res["status"] == 200 else None), **kw)
        return res, (recs or [])

    # 2. Contas a receber em aberto
    print("2. Contas a receber em aberto")
    _, open_now = fetch("2a", "Em aberto - mês atual", "/v4/Titulos/{ID}/TitulosSemBaixa/{inicio}/{fim}",
                        "/v4/Titulos/%s/TitulosSemBaixa/%s/%s" % (E, iso(m_ini), iso(m_fim)))
    _, open_60 = fetch("2b", "Em aberto - últimos 60 dias", "/v4/Titulos/{ID}/TitulosSemBaixa/{inicio}/{fim}",
                       "/v4/Titulos/%s/TitulosSemBaixa/%s/%s" % (E, iso(d60), iso(yesterday)))

    # 3. Recebimentos do mês anterior
    print("3. Recebimentos")
    _, received = fetch("3", "Recebimentos - mês anterior", "/v4/Titulos/{ID}/recebidos/{inicio}/{fim}",
                        "/v4/Titulos/%s/recebidos/%s/%s" % (E, iso(p_ini), iso(p_fim)))

    # 4. Saídas
    print("4. Saídas do caixa")
    _, outs = fetch("4", "Saídas (a pagar) - mês anterior", "/v1/Titulos/ObterTitulosAPagar/{ID}?DataInicio=&DataFim=",
                    "/v1/Titulos/ObterTitulosAPagar/%s?DataInicio=%s&DataFim=%s" % (E, iso(p_ini), iso(p_fim)))

    # 5/6. Agenda
    print("5/6. Agenda")
    a_fim = today + timedelta(days=2)
    _, ag5 = fetch("5", "Agenda v5 (com paciente)", "/v5/Estabelecimentos/{ID}/Agenda/0/{hoje}/{hoje+2}",
                   "/v5/Estabelecimentos/%s/Agenda/0/%s/%s" % (E, iso(today), iso(a_fim)))
    _, ag6 = fetch("6", "Agenda v6 (com situação)", "/v6/Agendamento/Estabelecimento/{ID}/{hoje}/{hoje+2}",
                   "/v6/Agendamento/Estabelecimento/%s/%s/%s" % (E, iso(today), iso(a_fim)))
    _, ag6b = fetch("6b", "Agenda v6 - 30 dias atrás (só p/ achar valores de situação)",
                    "/v6/Agendamento/Estabelecimento/{ID}/{hoje-30}/{hoje}",
                    "/v6/Agendamento/Estabelecimento/%s/%s/%s" % (E, iso(today - timedelta(days=30)), iso(today)))

    # 7. Orçamentos
    print("7. Orçamentos")
    _, orc = fetch("7", "Orçamentos - último mês", "/v4/Orcamentos/Orcamentos/{ID}/{inicio}/{fim}",
                   "/v4/Orcamentos/Orcamentos/%s/%s/%s" % (E, iso(today - timedelta(days=30)), iso(today)))

    # 8. Pacientes
    print("8. Pacientes")
    _, pac1 = fetch("8a", "Pacientes - ListaPessoasAnalitico", "/v1/Pessoa/ListaPessoasAnalitico/1/20/{ID}",
                    "/v1/Pessoa/ListaPessoasAnalitico/1/20/%s" % E)
    _, pac2 = fetch("8b", "Pacientes - ObterPessoasPeloEstabelecimento",
                    "/v1/Pessoa/ObterPessoasPeloEstabelecimento/1/20/{ID}",
                    "/v1/Pessoa/ObterPessoasPeloEstabelecimento/1/20/%s" % E)

    # 9. Profissionais
    print("9. Profissionais")
    _, prof = fetch("9", "Profissionais da agenda", "/v4/Estabelecimentos/{ID}/ProfissionaisAgenda",
                    "/v4/Estabelecimentos/%s/ProfissionaisAgenda" % E)

    analyse(rep, today, p_ini, p_fim, open_now, open_60, received, ag5, ag6, ag6b, orc, pac1, pac2)
    return rep


def analyse(rep, today, p_ini, p_fim, open_now, open_60, received, ag5, ag6, ag6b, orc, pac1, pac2):
    ex = rep.extra

    # --- Recebidos por forma de pagamento
    ex["recebidos"] = None
    if received:
        r0 = received[0]
        esp = pick_key(r0, ("especieNome", "nomeEspecie"), r"especie.*nome|nome.*especie") or pick_key(r0, (), r"especie|forma")
        val = pick_key(r0, ("valorRecebido", "valorPago", "valorBaixa", "valorLiquido", "valor"), r"valor")
        tot = collections.OrderedDict()
        if esp and val:
            for r in received:
                n = parse_num(r.get(val))
                k = str(r.get(esp))
                s, q = tot.get(k, (0.0, 0))
                tot[k] = (s + (n or 0.0), q + 1)
        ex["recebidos"] = {"campo_forma": esp, "campo_valor": val, "totais": tot}

    # --- Em aberto vencido
    ex["vencido"] = None
    src = open_60
    if src:
        r0 = src[0]
        dk = pick_key(r0, ("dataVencimento", "vencimento"), r"vencimento")
        vk = pick_key(r0, ("valor", "valorAberto", "saldo", "valorTitulo"), r"valor|saldo")
        soma, qtd, sem_data = 0.0, 0, 0
        if dk and vk:
            for r in src:
                d = parse_date(r.get(dk))
                if d is None:
                    sem_data += 1
                elif d < today:
                    soma += parse_num(r.get(vk)) or 0.0
                    qtd += 1
        ex["vencido"] = {"campo_data": dk, "campo_valor": vk, "soma": soma, "qtd": qtd, "sem_data": sem_data}

    # --- (a) telefone das contas em aberto
    ex["fone_titulos"] = phone_summary(open_now + open_60)
    ex["id_paciente_titulos"] = None
    if open_now or open_60:
        r0 = (open_now + open_60)[0]
        ex["id_paciente_titulos"] = pick_key(r0, ("pacienteId", "pessoaId", "clienteId"), r"(paciente|pessoa|cliente).*id$")

    # --- (b) agenda v5 x v6
    def ids(recs):
        return {str(r["id"]) for r in recs if "id" in r}
    i5, i6 = ids(ag5), ids(ag6)
    ex["join"] = {"n5": len(ag5), "n6": len(ag6), "ids5": len(i5), "ids6": len(i6),
                  "comum": len(i5 & i6), "so5": len(i5 - i6), "so6": len(i6 - i5)}

    # --- situação da agenda
    sit = collections.Counter()
    sit_keys = set()
    for r in ag6 + ag6b + ag5:
        for k, v in r.items():
            if re.search(r"situacao|status", k, re.I):
                sit_keys.add(k)
                if isinstance(v, dict):
                    v = v.get("nome") or v.get("descricao") or json.dumps(v, ensure_ascii=False)
                sit[(k, str(v))] += 1
    ex["situacao"] = (sit_keys, sit)

    # --- (c) orçamentos
    ex["orc"] = None
    if orc:
        r0 = orc[0]
        dk = pick_key(r0, ("dataAprovacao",), r"aprovacao")
        sk = pick_key(r0, (), r"situacao|status|aprovado")
        vazio = sentinela = preenchido = 0
        cross = collections.Counter()
        for r in orc:
            v = r.get(dk) if dk else None
            if v in (None, ""):
                vazio += 1
                filled = "vazia"
            elif (parse_date(v) or date(2000, 1, 1)).year <= 1901:
                sentinela += 1
                filled = "data-padrão (0001-01-01)"
            else:
                preenchido += 1
                filled = "preenchida"
            if sk:
                cross[(str(r.get(sk)), filled)] += 1
        ex["orc"] = {"campo_data": dk, "campo_situacao": sk, "vazio": vazio, "sentinela": sentinela,
                     "preenchido": preenchido, "cross": cross}

    # --- pacientes
    ex["pac"] = {"8a": phone_summary(pac1), "8b": phone_summary(pac2), "n8a": len(pac1), "n8b": len(pac2)}


def money(x):
    return "R$ {:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", ".")


def build_markdown(rep, est_count, today, refresh_ok, login_res, refresh_res):
    ex = rep.extra
    L = []
    w = L.append
    w("# Relatório de teste da API — Controle Odonto")
    w("")
    w("Gerado em %s. Teste **somente leitura**. Dados de pacientes mascarados "
      "(nome = iniciais, telefone = DDD + 2 últimos dígitos, CPF/e-mail/endereço/observações ocultos)." % datetime.now().strftime("%d/%m/%Y %H:%M"))
    w("")
    w("## 1. Resultado por endpoint")
    w("")
    w("| # | Endpoint | Status | Funcionou? | Qtd. registros | Tempo |")
    w("|---|----------|--------|------------|----------------|-------|")
    w("| 1a | POST /v4/Auth/co (login) | %s | %s | - | %d ms |" % (
        login_res["status"], "sim" if login_res["status"] == 200 else "NÃO", login_res["ms"]))
    w("| 1b | POST /v4/Auth/refresh/co (renovar) | %s | %s | - | %d ms |" % (
        refresh_res["status"], "sim" if refresh_ok else "NÃO", refresh_res["ms"]))
    for num, name, tpl, st, ok, cnt, ms in rep.rows:
        w("| %s | %s — `%s` | %s | %s | %s | %s |" % (num, name, tpl.replace("|", "\\|"), st, ok, cnt, ms))
    w("")
    w("## 2. Exemplo de um registro de cada endpoint (mascarado)")
    w("")
    w("Mostra os nomes dos campos e o formato dos valores (ex.: número `80.0` x texto `\"80,00\"`).")
    for num, name, tpl, sample in rep.samples:
        w("")
        w("### %s — %s" % (num, name))
        w("```json")
        w(json.dumps(sample, ensure_ascii=False, indent=2))
        w("```")
    w("")
    w("## 3. Valores possíveis do campo de situação da agenda")
    w("")
    keys, sit = ex["situacao"]
    if sit:
        w("Campos encontrados: %s. Valores vistos (agenda de hoje a +2 dias e mais 30 dias para trás):" % ", ".join("`%s`" % k for k in sorted(keys)))
        w("")
        w("| Campo | Valor | Ocorrências |")
        w("|-------|-------|-------------|")
        for (k, v), n in sit.most_common():
            w("| %s | %s | %d |" % (k, v, n))
        w("")
        w("> Só aparecem os valores que existiam nesse período. Podem existir outros (ex.: cancelado, remarcado) ainda não vistos.")
    else:
        w("Nenhum campo de situação encontrado (ou agenda vazia no período).")
    w("")
    w("## 4. Totais do mês anterior")
    w("")
    r = ex["recebidos"]
    if r and r["totais"]:
        w("**Recebidos por forma de pagamento** (campo da forma: `%s`, campo do valor: `%s`):" % (r["campo_forma"], r["campo_valor"]))
        w("")
        w("| Forma de pagamento | Qtd. | Total |")
        w("|--------------------|------|-------|")
        total = 0.0
        for k, (s, q) in r["totais"].items():
            w("| %s | %d | %s |" % (k, q, money(s)))
            total += s
        w("| **Total geral** | | **%s** |" % money(total))
    else:
        w("Recebidos: não foi possível totalizar (sem dados ou campos de forma de pagamento/valor não identificados — confira os exemplos acima).")
    w("")
    v = ex["vencido"]
    if v and v["campo_data"] and v["campo_valor"]:
        w("**Total em aberto vencido** (últimos 60 dias, vencimento anterior a hoje; campos `%s` e `%s`): **%s** em %d título(s)%s." % (
            v["campo_data"], v["campo_valor"], money(v["soma"]), v["qtd"],
            "; %d sem data de vencimento reconhecível" % v["sem_data"] if v["sem_data"] else ""))
    else:
        w("Total em aberto vencido: não calculado (sem dados ou campos de vencimento/valor não identificados).")
    w("")
    w("## 5. Respostas diretas")
    w("")
    keys_t, best_t, fmts_t = ex["fone_titulos"]
    total_t = sum(best_t.values())
    w("**(a) O telefone das contas em aberto é celular com DDD utilizável no WhatsApp?**")
    w("")
    if total_t == 0:
        w("Sem títulos em aberto para analisar.")
    else:
        cel = best_t.get("celular com DDD", 0)
        w("- Campos de telefone nos títulos: %s" % (", ".join("`%s`" % k for k in keys_t) or "**nenhum**"))
        w("- Classificação (por título): " + "; ".join("%s = %d" % (k, n) for k, n in best_t.most_common()))
        for k, n in fmts_t.most_common(5):
            w("- Formato visto: `%s` (%d)" % (k, n))
        if keys_t:
            w("- **Conclusão: %s** (%d de %d títulos com celular com DDD)." % (
                "SIM" if cel == total_t else ("PARCIALMENTE" if cel else "NÃO"), cel, total_t))
        else:
            w("- **Conclusão: NÃO diretamente** — os títulos não trazem telefone. %s" % (
                "Há o campo `%s`, que permite buscar o telefone no cadastro do paciente." % ex["id_paciente_titulos"]
                if ex["id_paciente_titulos"] else "Não achei campo de ID do paciente para cruzar com o cadastro."))
    w("")
    j = ex["join"]
    w("**(b) Dá para juntar agenda v5 e v6 pelo `id`?**")
    w("")
    w("- v5: %d registros (%d com `id`); v6: %d registros (%d com `id`)." % (j["n5"], j["ids5"], j["n6"], j["ids6"]))
    w("- ids em comum: %d; só na v5: %d; só na v6: %d." % (j["comum"], j["so5"], j["so6"]))
    if j["n5"] == 0 and j["n6"] == 0:
        w("- **Conclusão: inconclusivo** — sem agendamentos no período. Repita em um período com agenda.")
    else:
        w("- **Conclusão: %s**." % ("SIM, todos os ids batem" if j["ids5"] and j["so5"] == 0 and j["so6"] == 0 and j["comum"] else
                                    ("PARCIALMENTE" if j["comum"] else "NÃO")))
    w("")
    o = ex["orc"]
    w("**(c) Dá para identificar orçamentos não aprovados?**")
    w("")
    if o:
        w("- Campo de data: `%s`; campo de situação/aprovação: `%s`." % (o["campo_data"], o["campo_situacao"]))
        w("- `dataAprovacao` vazia/nula: %d; com data-padrão (ex.: 0001-01-01): %d; preenchida: %d." % (o["vazio"], o["sentinela"], o["preenchido"]))
        if o["cross"]:
            w("- Cruzamento situação x data: " + "; ".join("%s / %s = %d" % (a, b, n) for (a, b), n in o["cross"].most_common()))
        w("- **Conclusão: %s**." % ("SIM — não aprovados vêm com data vazia/padrão" if (o["vazio"] or o["sentinela"]) and o["campo_data"] else
                                    "não ficou claro (todos têm data de aprovação ou o campo não existe)"))
    else:
        w("Sem orçamentos no período; inconclusivo.")
    w("")
    w("### Pacientes — qual endpoint traz telefone?")
    w("")
    for k, label in (("8a", "ListaPessoasAnalitico"), ("8b", "ObterPessoasPeloEstabelecimento")):
        kk, bb, ff = ex["pac"][k]
        w("- **%s** (%d registros): campos de telefone: %s. Classificação: %s." % (
            label, ex["pac"]["n" + k], ", ".join("`%s`" % x for x in kk) or "nenhum",
            "; ".join("%s = %d" % (a, n) for a, n in bb.most_common()) or "-"))
        for fk, n in ff.most_common(4):
            w("  - formato: `%s` (%d)" % (fk, n))
    w("")
    w("## 6. Erros, limites e comportamentos diferentes do esperado")
    w("")
    w("- Login com %d local(is) em `outrosLocais`; usado o primeiro." % est_count)
    w("- Renovação do token: %s." % ("funcionou" if refresh_ok else "FALHOU (status %s)" % refresh_res["status"]))
    if rep.notes:
        for n in rep.notes:
            w("- " + n)
    else:
        w("- Nenhum erro nas chamadas.")
    w("- Campos com `descri*`, `observ*`, endereço e documentos são ocultados por padrão neste relatório (podem conter dados pessoais).")
    w("")
    return "\n".join(L)


def main():
    if "--selftest" in sys.argv:
        return selftest()
    out = "RELATORIO_TESTE_API.md"
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    user, pwd = os.environ.get("CO_USER"), os.environ.get("CO_PASS")
    if not user or not pwd:
        print("Faltam as variáveis CO_USER e CO_PASS. No terminal, rode:\n"
              '  export CO_USER="seu_usuario"\n  export CO_PASS="sua_senha"\nE depois execute de novo.')
        return 2

    api = Api()
    print("1. Login e renovação do token")
    login_res = api.login(user, pwd)
    del pwd
    print("   login: status=%s (%d ms)" % (login_res["status"], login_res["ms"]))
    if not api.token:
        print("   Login falhou (%s). Não vou tentar de novo para não bloquear o usuário." % (login_res["detail"] or login_res["error"] or ""))
        return 1
    print("   token (10 primeiros caracteres): %s…" % api.token[:10])

    d = login_res["json"]["data"]
    locais = d.get("outrosLocais") or []
    ids = [l.get("estabelecimentoID") for l in locais if isinstance(l, dict) and l.get("estabelecimentoID") is not None]
    est = os.environ.get("CO_EST_ID") or (ids[0] if ids else d.get("estabelecimentoID") or d.get("estabelecimentoId"))
    if not est:
        print("   Não achei estabelecimentoID no login.")
        return 1
    print("   estabelecimentos no login: %d; usando o primeiro." % len(ids))

    refresh_res = api.refresh()
    refresh_ok = refresh_res["status"] == 200 and api.token and refresh_res["json"] is not None
    print("   renovação: status=%s (%d ms); novo token: %s…" % (refresh_res["status"], refresh_res["ms"], api.token[:10]))

    rep = run(api, est)
    rep.notes.insert(0, "429 (limite de chamadas) ocorreu %d vez(es)." % api.n429)
    md = sanitize_text(build_markdown(rep, len(ids), date.today(), refresh_ok, login_res, refresh_res))
    for secret in (api.token, api.refresh_token):
        if secret and secret in md:
            md = md.replace(secret, "[oculto]")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("\nPronto! Relatório (mascarado) salvo em: %s" % out)
    return 0


# ----------------------------------------------------------------------------
# Autoteste do mascaramento (sem rede, sem credenciais)
# ----------------------------------------------------------------------------
def selftest():
    rec = {"id": 7, "nomePaciente": "Maria da Silva Santos", "celular": "(12) 99876-5434",
           "telefone": 12998765434, "cpf": "123.456.789-09", "email": "maria@x.com",
           "especieNome": "Cartão de Crédito", "valor": 80.0, "valorTxt": "80,00",
           "dataAprovacao": None, "situacao": "Confirmado", "observacao": "alergia a X",
           "contato": {"mensagem": "oi"}, "accessToken": "abcdefghijklmnopqrstuvwxyz",
           "nota": "fale com joao@teste.com"}
    m = mask(rec)
    assert m["nomePaciente"] == "M.S.S.", m
    assert m["celular"] == "(12) 9****-**34", m
    assert m["telefone"] == "(12) 9****-**34", m
    assert m["cpf"] == m["email"] == m["observacao"] == "[oculto]", m
    assert m["especieNome"] == "Cartão de Crédito" and m["valor"] == 80.0 and m["situacao"] == "Confirmado"
    assert m["accessToken"] == "abcdefghij…", m
    assert m["nota"] == "[oculto]"
    assert m["contato"] == {"mensagem": "[oculto]"}
    assert mask_phone("1234567") == "(sem DDD) ****-**67"
    assert parse_num("1.234,50") == 1234.5 and parse_num(80.0) == 80.0 and parse_num("80,00") == 80.0
    assert parse_date("2026-10-05T00:00:00") == date(2026, 10, 5) and parse_date("05/10/2026") == date(2026, 10, 5)
    assert classify_phone("(12) 99876-5434") == "celular com DDD" and classify_phone("") == "vazio"
    assert fmt_pattern("(12) 99876-5434") == "str:(99) 99999-9999"
    assert find_records({"data": [{"dia": "1", "itens": [{"id": 1}, {"id": 2}]}]}) == [{"id": 1}, {"id": 2}]
    assert find_records({"data": {"lista": [{"id": 1}], "total": 1}}) == [{"id": 1}]
    print("Autoteste OK: mascaramento e leitura de formatos funcionando.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
