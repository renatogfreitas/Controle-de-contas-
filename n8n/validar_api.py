"""Valida login + agenda de amanhã do Controle Odonto.
Lê usuário/senha SOMENTE das variáveis de ambiente CO_USER e CO_PASS.
Não imprime token, nomes nem telefones: só números agregados e nomes de campos."""
import json, os, sys, urllib.request, uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

user, pwd = os.environ.get("CO_USER"), os.environ.get("CO_PASS")
if not user or not pwd:
    sys.exit("Defina CO_USER e CO_PASS no ambiente.")

b = uuid.uuid4().hex
body = "".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n' for k, v in (("Nome", user), ("Senha", pwd))) + f"--{b}--\r\n"
req = urllib.request.Request("https://api.aplicativo.net/v4/Auth/co", data=body.encode(), method="POST",
                             headers={"Content-Type": f"multipart/form-data; boundary={b}"})
login = json.load(urllib.request.urlopen(req))["data"]
token, est = login["accessToken"], login["outrosLocais"][0]["estabelecimentoID"]
print("Login OK. estabelecimentoID encontrado.")

amanha = (datetime.now(ZoneInfo("America/Sao_Paulo")) + timedelta(days=1)).strftime("%Y-%m-%d")
req = urllib.request.Request(f"https://api.aplicativo.net/v6/Agendamento/Estabelecimento/{est}/{amanha}/{amanha}",
                             headers={"Authorization": f"Bearer {token}"})
r = urllib.request.urlopen(req)
print("Agenda", amanha, "-> HTTP", r.status)
raw = r.read().decode()
dados = json.loads(raw)["data"] if raw.strip() else []
print("Total:", len(dados))
if dados:
    print("Campos do 1º registro (só nomes):", list(dados[0].keys()))
