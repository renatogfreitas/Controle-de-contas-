# Relatório de teste da API — Controle Odonto

Gerado em 19/11/2026 23:14. Teste **somente leitura**. Dados de pacientes mascarados (nome = iniciais, telefone = DDD + 2 últimos dígitos, CPF/e-mail/endereço/observações ocultos).

## 1. Resultado por endpoint

| # | Endpoint | Status | Funcionou? | Qtd. registros | Tempo |
|---|----------|--------|------------|----------------|-------|
| 1a | POST /v4/Auth/co (login) | 200 | sim | - | 767 ms |
| 1b | POST /v4/Auth/refresh/co (renovar) | 200 | sim | - | 506 ms |
| 2a | Em aberto - mês atual — `/v4/Titulos/{ID}/TitulosSemBaixa/{inicio}/{fim}` | 200 | sim | 700 | 1008 ms |
| 2b | Em aberto - últimos 60 dias — `/v4/Titulos/{ID}/TitulosSemBaixa/{inicio}/{fim}` | 200 | sim | 1104 | 1097 ms |
| 3 | Recebimentos - mês anterior — `/v4/Titulos/{ID}/recebidos/{inicio}/{fim}` | 200 | sim | 433 | 1005 ms |
| 4 | Saídas (a pagar) - mês anterior — `/v1/Titulos/ObterTitulosAPagar/{ID}?DataInicio=&DataFim=` | 204 | sim (204 = sem dados) | 0 | 538 ms |
| 5 | Agenda v5 (com paciente) — `/v5/Estabelecimentos/{ID}/Agenda/0/{hoje}/{hoje+2}` | 200 | sim | 56 | 758 ms |
| 6 | Agenda v6 (com situação) — `/v6/Agendamento/Estabelecimento/{ID}/{hoje}/{hoje+2}` | 200 | sim | 56 | 745 ms |
| 6b1 | Agenda v6 - janela extra 1 (só p/ achar valores de situação) — `/v6/Agendamento/Estabelecimento/{ID}/{hoje-27}/{hoje-19}` | 200 | sim | 169 | 995 ms |
| 6b2 | Agenda v6 - janela extra 2 (só p/ achar valores de situação) — `/v6/Agendamento/Estabelecimento/{ID}/{hoje-18}/{hoje-10}` | 200 | sim | 91 | 832 ms |
| 6b3 | Agenda v6 - janela extra 3 (só p/ achar valores de situação) — `/v6/Agendamento/Estabelecimento/{ID}/{hoje-9}/{hoje-1}` | 200 | sim | 125 | 848 ms |
| 6b4 | Agenda v6 - janela extra 4 (só p/ achar valores de situação) — `/v6/Agendamento/Estabelecimento/{ID}/{hoje+3}/{hoje+11}` | 200 | sim | 115 | 856 ms |
| 7 | Orçamentos - último mês — `/v4/Orcamentos/Orcamentos/{ID}/{inicio}/{fim}` | 200 | sim | 182 | 1738 ms |
| 8a | Pacientes - ListaPessoasAnalitico — `/v1/Pessoa/ListaPessoasAnalitico/1/20/{ID}` | 200 | sim | 20 | 510 ms |
| 8b | Pacientes - ObterPessoasPeloEstabelecimento — `/v1/Pessoa/ObterPessoasPeloEstabelecimento/1/20/{ID}` | 200 | sim | 20 | 536 ms |
| 9 | Profissionais da agenda — `/v4/Estabelecimentos/{ID}/ProfissionaisAgenda` | 200 | sim | 13 | 666 ms |

## 2. Exemplo de um registro de cada endpoint (mascarado)

Mostra os nomes dos campos e o formato dos valores (ex.: número `80.0` x texto `"80,00"`).

### 2a — Em aberto - mês atual
```json
{
  "id": 77516092,
  "dataVencimento": "2026-11-09T00:00:00",
  "documento": "[oculto]",
  "sequencia": 24,
  "valorDevido": 24.9,
  "valorOriginal": 24.9,
  "consumidorID": 21756149,
  "consumidorApelido": "S.A.",
  "consumidorNomeCompleto": "S.A.C.S.",
  "planoContaNome": "Consulta Odontológica",
  "especieNome": "Carteira",
  "especieSequencia": 2,
  "telefone": "(12) 9****-**82"
}
```
Campos que NÃO vêm em todos os registros: documento (693 de 700), sequencia (695 de 700), planoContaNome (634 de 700), contratoID (603 de 700), observacoes (247 de 700), parcelas (376 de 700), convenioID (217 de 700), conevenioNome (217 de 700), responsavelNomeCompleto (63 de 700)

### 2b — Em aberto - últimos 60 dias
```json
{
  "id": 77516092,
  "dataVencimento": "2026-11-09T00:00:00",
  "documento": "[oculto]",
  "sequencia": 24,
  "valorDevido": 24.9,
  "valorOriginal": 24.9,
  "consumidorID": 21756149,
  "consumidorApelido": "S.A.",
  "consumidorNomeCompleto": "S.A.C.S.",
  "planoContaNome": "Consulta Odontológica",
  "especieNome": "Carteira",
  "especieSequencia": 2,
  "telefone": "(12) 9****-**82"
}
```
Campos que NÃO vêm em todos os registros: documento (1098 de 1104), sequencia (1100 de 1104), planoContaNome (967 de 1104), contratoID (936 de 1104), observacoes (492 de 1104), parcelas (506 de 1104), convenioID (295 de 1104), conevenioNome (295 de 1104), responsavelNomeCompleto (72 de 1104)

### 3 — Recebimentos - mês anterior
```json
{
  "id": 92672560,
  "data": "2026-10-01T00:00:00",
  "pagoValor": 109.99,
  "pagoMulta": 0.0,
  "pagoJuros": 0.0,
  "pagoDescontos": 10.0,
  "dataVencimento": "2026-10-01T00:00:00",
  "documento": "[oculto]",
  "sequencia": 30,
  "contaBancariaID": 52319,
  "consumidorID": 21746757,
  "consumidorApelido": "L.",
  "consumidorNomeCompleto": "L.M.A.",
  "contratoID": 17853667,
  "especieID": 1,
  "planoContasID": 53,
  "recebivelID": 77415067,
  "manutencao": true,
  "transacaoID": 1,
  "especieNome": "Dinheiro",
  "especieSequencia": 1,
  "planoContaNome": "Manutenção Ortodôntica",
  "financeiroID": 30769069
}
```
Campos que NÃO vêm em todos os registros: pagoMulta (331 de 433), pagoJuros (336 de 433), pagoDescontos (298 de 433), documento (413 de 433), sequencia (413 de 433), contratoID (376 de 433), recebivelID (425 de 433), manutencao (206 de 433), parcelas (316 de 433), tarifaID (306 de 433), convenioID (152 de 433), medicoID (320 de 433), prontuarioControle (169 de 433), tarifaNome (306 de 433), convenioNome (152 de 433), medicoApelido (320 de 433), responsavelNomeCompleto (62 de 433), dataOcorrencia (68 de 433), pagoDespesas (68 de 433), observacoes (16 de 433), especieParcela (8 de 433), especieParcelas (8 de 433), especiePreDatado (8 de 433)

### 5 — Agenda v5 (com paciente)
```json
{
  "id": 145004599,
  "dataInicio": "2026-11-19T09:00:00",
  "dataTermino": "2026-11-19T09:45:00",
  "diaTodo": false,
  "consumidorId": 30552365,
  "consumidorPessoaId": 31710829,
  "consumidorPessoaNome": "D.A.R.",
  "consumidorPessoaFone1": "(12) 9****-**18",
  "consumidorPessoaFone1Sms": true,
  "consumidorPessoaFone2Sms": false,
  "consumidorPessoaEmail": "[oculto]",
  "consumidorPessoaDataNascimento": "[oculto]",
  "descricao": "[oculto]",
  "funcionarioId": 224793,
  "estabelecimentoId": 18633,
  "pessoaId": 26707048,
  "atendimentoId": 101745235,
  "atendimentoTipoCustomId": 0,
  "atendeTipoId": 1,
  "atendimentoTipoNome": "Avaliação - Clínico",
  "salaId": 34678,
  "secretariaId": 194235,
  "solucaoId": 1,
  "loginId": 76325908,
  "urlFotoPaciente": "[oculto]",
  "atendimentoDataChegada": "2026-11-19T09:13:00",
  "atendimentoDataInicio": "2026-11-19T09:37:00",
  "atendimentoDataTermino": "2026-11-19T09:38:00"
}
```
Campos que NÃO vêm em todos os registros: consumidorPessoaEmail (42 de 56), consumidorPessoaDataNascimento (41 de 56), descricao (34 de 56), atendimentoId (23 de 56), atendimentoDataChegada (23 de 56), atendimentoDataInicio (23 de 56), atendimentoDataTermino (23 de 56), dataCancelamento (6 de 56), cancelamentoPessoaId (6 de 56), cancelamentoClinica (6 de 56), consumidorPessoaFone2 (18 de 56), reagendamentoId (1 de 56)

### 6 — Agenda v6 (com situação)
```json
{
  "id": 143507070,
  "estabelecimentoID": 18633,
  "dataInicio": "2026-11-21T08:00:00",
  "dataTermino": "2026-11-21T08:15:00",
  "situacao": "Agendado",
  "nomeCompleto": "W.L.S.",
  "contato": "(65) 9****-**85",
  "salaID": 34678,
  "funcionarioID": 232288,
  "apelido": "W.",
  "cargo": "Dentista",
  "especialidade": "Ortodontia",
  "thumbURL": "[oculto]",
  "numeroProntuario": "[oculto]",
  "tipoAtendimento": "Avaliação - Clínico",
  "tipoAtendimentoID": 1,
  "numeroSala": "03",
  "nomeSala": "S.",
  "dataCadastro": "2026-11-07T09:11:00",
  "estabelecimentoNome": "O.F.",
  "nomeDentista": "A.V.C.",
  "pessoaID": 27663429,
  "consumidorID": 25108596,
  "consumidorPessoaID": 26047738,
  "consumidorPessoaFone1": "(65) 9****-**85"
}
```
Campos que NÃO vêm em todos os registros: consumidorPessoaFone2 (18 de 56), descricao (34 de 56)

### 6b1 — Agenda v6 - janela extra 1 (só p/ achar valores de situação)
```json
{
  "id": 142750483,
  "estabelecimentoID": 18633,
  "dataInicio": "2026-10-27T16:00:00",
  "dataTermino": "2026-10-27T16:15:00",
  "situacao": "Atendido",
  "nomeCompleto": "S.C.S.S.",
  "contato": "(43) 9****-**98",
  "salaID": 34679,
  "funcionarioID": 194780,
  "apelido": "S.",
  "cargo": "Dentista",
  "especialidade": "Endodontia",
  "thumbURL": "[oculto]",
  "numeroProntuario": "[oculto]",
  "tipoAtendimento": "Avaliação - Clínico",
  "tipoAtendimentoID": 1,
  "descricao": "[oculto]",
  "numeroSala": "04",
  "nomeSala": "S.",
  "dataCadastro": "2026-10-24T13:06:00",
  "estabelecimentoNome": "O.F.",
  "nomeDentista": "C.E.D.",
  "pessoaID": 22406132,
  "consumidorID": 30211853,
  "consumidorPessoaID": 31358175,
  "consumidorPessoaFone1": "(43) 9****-**98"
}
```
Campos que NÃO vêm em todos os registros: descricao (102 de 169), consumidorPessoaFone2 (36 de 169)

### 6b2 — Agenda v6 - janela extra 2 (só p/ achar valores de situação)
```json
{
  "id": 143017913,
  "estabelecimentoID": 18633,
  "dataInicio": "2026-11-03T15:00:00",
  "dataTermino": "2026-11-03T15:15:00",
  "situacao": "Atendido",
  "nomeCompleto": "A.P.O.V.",
  "contato": "(12) 9****-**48",
  "salaID": 34679,
  "funcionarioID": 194780,
  "apelido": "A.",
  "cargo": "Dentista",
  "especialidade": "Endodontia",
  "thumbURL": "[oculto]",
  "numeroProntuario": "",
  "tipoAtendimento": "Avaliação - Clínico",
  "tipoAtendimentoID": 1,
  "descricao": "[oculto]",
  "numeroSala": "04",
  "nomeSala": "S.",
  "dataCadastro": "2026-10-29T17:12:00",
  "estabelecimentoNome": "O.F.",
  "nomeDentista": "C.E.D.",
  "pessoaID": 22406132,
  "consumidorID": 21745397,
  "consumidorPessoaID": 22599836,
  "consumidorPessoaFone1": "(12) 9****-**48"
}
```
Campos que NÃO vêm em todos os registros: descricao (60 de 91), consumidorPessoaFone2 (17 de 91), tipoAtendimentoCustomID (2 de 91)

### 6b3 — Agenda v6 - janela extra 3 (só p/ achar valores de situação)
```json
{
  "id": 143144618,
  "estabelecimentoID": 18633,
  "dataInicio": "2026-11-10T13:00:00",
  "dataTermino": "2026-11-10T13:15:00",
  "situacao": "Desmarcado pelo Paciente",
  "nomeCompleto": "M.P.S.",
  "contato": "(12) 9****-**92",
  "salaID": 34679,
  "funcionarioID": 194780,
  "apelido": "M.",
  "cargo": "Dentista",
  "especialidade": "Endodontia",
  "thumbURL": "[oculto]",
  "numeroProntuario": "[oculto]",
  "tipoAtendimento": "Avaliação - Clínico",
  "tipoAtendimentoID": 1,
  "descricao": "[oculto]",
  "numeroSala": "04",
  "nomeSala": "S.",
  "dataCadastro": "2026-11-03T15:27:00",
  "estabelecimentoNome": "O.F.",
  "nomeDentista": "C.E.D.",
  "pessoaID": 22406132,
  "consumidorID": 29965932,
  "consumidorPessoaID": 31103849,
  "consumidorPessoaFone1": "(12) 9****-**92"
}
```
Campos que NÃO vêm em todos os registros: descricao (77 de 125), consumidorPessoaFone2 (23 de 125)

### 6b4 — Agenda v6 - janela extra 4 (só p/ achar valores de situação)
```json
{
  "id": 142893100,
  "estabelecimentoID": 18633,
  "dataInicio": "2026-11-24T17:00:00",
  "dataTermino": "2026-11-24T17:15:00",
  "situacao": "Agendado",
  "nomeCompleto": "M.I.P.S.",
  "contato": "(12) 9****-**15",
  "salaID": 34679,
  "funcionarioID": 194780,
  "apelido": "M.",
  "cargo": "Dentista",
  "especialidade": "Endodontia",
  "thumbURL": "[oculto]",
  "numeroProntuario": "",
  "tipoAtendimento": "Avaliação - Clínico",
  "tipoAtendimentoID": 1,
  "descricao": "[oculto]",
  "numeroSala": "04",
  "nomeSala": "S.",
  "dataCadastro": "2026-10-27T16:39:00",
  "estabelecimentoNome": "O.F.",
  "nomeDentista": "C.E.D.",
  "pessoaID": 22406132,
  "consumidorID": 21743720,
  "consumidorPessoaID": 22598159,
  "consumidorPessoaFone1": "(12) 9****-**15"
}
```
Campos que NÃO vêm em todos os registros: descricao (48 de 115), consumidorPessoaFone2 (25 de 115), tipoAtendimentoCustomID (1 de 115)

### 7 — Orçamentos - último mês
```json
{
  "id": 33060431,
  "dataEmissao": "2026-10-20T00:00:00",
  "dataValidade": "2026-11-20T00:00:00",
  "totalProcedimentosClinicos": 40800.0,
  "totalProcedimentosOrto": 0.0,
  "totalManutencaoOrto": 0.0,
  "outrosDescontos": 25800.0,
  "atendimentosID": 99947616,
  "atendimentos": {
    "id": 99947616,
    "atendeTipoID": 1,
    "descAtedimentoTipo": "Avaliação - Clínico",
    "dataInclusao": "2026-10-20T11:08:00",
    "dataChegada": "2026-10-20T11:08:00",
    "dataInicio": "2026-10-20T11:20:00",
    "dataTermino": "2026-10-20T11:39:00",
    "consumidorID": 30206784
  },
  "consumidores": {
    "id": 30206784,
    "pessoaID": 31352808,
    "nome": "E.C.L.",
    "dataInclusao": "2026-10-20T11:08:00"
  },
  "consumidorID": 30206784,
  "pacienteNovo": false,
  "planoContasId": 40,
  "planoContasNome": "Serviços Odontológicos",
  "listaOrcamentosItens": [
    {
      "orcamentoID": 33060431,
      "valorUnitario": 3800.0
    },
    {
      "orcamentoID": 33060431,
      "valorUnitario": 30000.0
    }
  ],
  "listaOrcamentosParcelas": [
    {
      "orcamentoID": 33060431,
      "modoPagamento": "A Vista",
      "numeroParcela": 1,
      "dias": 0,
      "qtdTotalParcelas": 25,
      "titulosEspecies": "Carteira",
      "valor": 2000.0,
      "valorTotalParcelas": 15000.0
    },
    {
      "orcamentoID": 33060431,
      "modoPagamento": "Dia(s)",
      "numeroParcela": 2,
      "dias": 31,
      "qtdTotalParcelas": 25,
      "titulosEspecies": "Carteira",
      "valor": 541.67,
      "valorTotalParcelas": 15000.0
    }
  ]
}
```
Campos que NÃO vêm em todos os registros: totalProcedimentosOrto (96 de 182), totalManutencaoOrto (65 de 182), outrosDescontos (114 de 182), atendimentosID (144 de 182), atendimentos (144 de 182), dataAprovacao (71 de 182), manutencaoDia (18 de 182), manutencaoCarencia (18 de 182), outrasDespesas (6 de 182)

### 8a — Pacientes - ListaPessoasAnalitico
```json
{
  "id": 21616001,
  "nomeCompleto": "A.F.",
  "email": "[oculto]",
  "contato": "(21) 9****-**45",
  "estabelecimentoID": 18633,
  "sexo": false,
  "endereco": "[oculto]",
  "dataInclusao": "2024-12-13T08:29:00"
}
```
Campos que NÃO vêm em todos os registros: email (11 de 20), endereco (19 de 20), dataNascimento (9 de 20), responsavel (1 de 20)

### 8b — Pacientes - ObterPessoasPeloEstabelecimento
```json
{
  "id": "31747062",
  "nomeCompleto": "A.R.N.",
  "cpf": "[oculto]",
  "sexo": "Masculino",
  "dataNascimento": "[oculto]",
  "guid": "[oculto]",
  "email": "[oculto]",
  "responsavelFinanceiro": "",
  "endereco": "",
  "telefone": "",
  "fotoUrl": "[oculto]",
  "parentes": [],
  "relacionamentos": [],
  "dataCadastro": "2026-11-19T18:25:00"
}
```
Campos que NÃO vêm em todos os registros: cpf (19 de 20), dataNascimento (18 de 20), email (12 de 20), rg (9 de 20), estadoCivil (3 de 20)

### 9 — Profissionais da agenda
```json
{
  "funcionarioID": 190865,
  "pessoaID": 21767365,
  "nomeCompleto": "B.G.F.",
  "apelido": "D.B.F.",
  "fotoUrl": "[oculto]",
  "agendaIntervalo": 15,
  "cargoID": 3,
  "cargoNome": "Dentista",
  "horarios": [
    {
      "salaID": 34676,
      "domingo": false,
      "segunda": true,
      "terca": true,
      "quarta": true,
      "quinta": true,
      "sexta": true,
      "sabado": false,
      "inicio": "1900-01-01T10:00:00",
      "termino": "1900-01-01T12:00:00",
      "permiteAgenda": true
    },
    {
      "salaID": 34676,
      "domingo": false,
      "segunda": false,
      "terca": false,
      "quarta": false,
      "quinta": false,
      "sexta": false,
      "sabado": true,
      "inicio": "1900-01-01T10:00:00",
      "termino": "1900-01-01T13:30:00",
      "permiteAgenda": true
    }
  ]
}
```
Campos que NÃO vêm em todos os registros: agendaIntervalo (10 de 13)

## 3. Valores possíveis do campo de situação da agenda

Campos encontrados: `situacao`. Valores vistos (hoje a +2 dias, 27 dias para trás e 3 a 11 dias à frente):

| Campo | Valor | Ocorrências |
|-------|-------|-------------|
| situacao | Atendido | 269 |
| situacao | Agendado | 143 |
| situacao | Faltou sem justificada | 90 |
| situacao | Desmarcado pelo Paciente | 54 |

> Só aparecem os valores que existiam nesse período. Podem existir outros (ex.: cancelado, remarcado) ainda não vistos.

## 4. Totais do mês anterior

**Recebidos por forma de pagamento** (campo da forma: `especieNome`, campo do valor: `pagoValor`):

| Forma de pagamento | Qtd. | Total |
|--------------------|------|-------|
| Dinheiro | 127 | R$ 24.595,41 |
| Cartão de Crédito - Recorrente | 111 | R$ 10.006,42 |
| Cartão de Débito | 91 | R$ 13.925,66 |
| Compensação de Boleto | 68 | R$ 10.055,05 |
| Crédito em Conta | 12 | R$ 2.867,99 |
| Cartão de Crédito - Rotativo | 16 | R$ 1.807,82 |
| Cartão de Crédito - Parcelado | 8 | R$ 12.900,00 |
| **Total geral** | | **R$ 76.158,35** |

Outros valores nos mesmos recebimentos (não incluídos acima): `pagoMulta` = R$ 87,02; `pagoJuros` = R$ 198,91; `pagoDescontos` = R$ 917,22

**Total em aberto vencido** (últimos 60 dias, vencimento anterior a hoje; campos `dataVencimento` e `valorDevido`): **R$ 121.564,95** em 1104 título(s).

## 5. Respostas diretas

**(a) O telefone das contas em aberto é celular com DDD utilizável no WhatsApp?**

- Campos de telefone nos títulos: `telefone`
- Classificação (por título): celular com DDD = 1765; formato estranho = 30; fixo com DDD = 6; vazio = 3
- Formato visto: `telefone -> str:99999999999` (1771)
- Formato visto: `telefone -> str:9999999999` (30)
- **Conclusão: PARCIALMENTE** (1765 de 1804 títulos com celular com DDD).

**(b) Dá para juntar agenda v5 e v6 pelo `id`?**

- v5: 56 registros (56 com `id`); v6: 56 registros (56 com `id`).
- ids em comum: 56; só na v5: 0; só na v6: 0.
- **Conclusão: SIM, todos os ids batem**.

**(c) Dá para identificar orçamentos não aprovados?**

- Total de orçamentos: 182. Campo de data de aprovação: `dataAprovacao`; campo de situação/status: `None`.
- `dataAprovacao` **ausente** (o campo nem vem no registro): 111; presente mas vazia/nula: 0; com data-padrão (ex.: 0001-01-01): 0; com data real: 71.
- **Conclusão: SIM — não aprovados = sem `dataAprovacao` (111 de 182). No n8n, teste se o campo existe/está vazio, não apenas se é nulo.**

### Pacientes — qual endpoint traz telefone?

- **ListaPessoasAnalitico** (20 registros): campos de telefone: `contato`. Classificação: vazio = 11; celular com DDD = 9.
  - formato: `contato -> int:9` (11)
  - formato: `contato -> int:99999999999` (9)
- **ObterPessoasPeloEstabelecimento** (20 registros): campos de telefone: `telefone`. Classificação: celular com DDD = 17; vazio = 3.
  - formato: `telefone -> str:99999999999` (17)

## 6. Erros, limites e comportamentos diferentes do esperado

- Login com 1 local(is) em `outrosLocais`; usado o primeiro.
- Renovação do token: funcionou.
- 429 (limite de chamadas) ocorreu 0 vez(es).
- Campos com `descri*`, `observ*`, endereço e documentos são ocultados por padrão neste relatório (podem conter dados pessoais).
