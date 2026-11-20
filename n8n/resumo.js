// ===== Nó "Resumo" =====
// Lê a resposta da agenda e devolve UM item com números e 3 exemplos MASCARADOS (LGPD).

const entrada = $input.all();
const amanha = $('Dados do login').first().json.amanha;

// 1) Juntar a lista de agendamentos (trata 204 = sem consultas)
let agendamentos = [];
let statusHttp = null;
for (const item of entrada) {
  const j = item.json || {};
  statusHttp = j.statusCode ?? statusHttp;
  let corpo = j.body ?? j.data ?? j;
  if (typeof corpo === 'string') {
    corpo = corpo.trim() === '' ? {} : JSON.parse(corpo);
  }
  if (Array.isArray(corpo)) agendamentos.push(...corpo);
  else if (corpo && Array.isArray(corpo.data)) agendamentos.push(...corpo.data);
}

// 2) Funções auxiliares
const semAcento = (t) => String(t ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const primeiro = (obj, campos) => { for (const c of campos) if (obj[c] !== undefined && obj[c] !== null && obj[c] !== '') return obj[c]; return null; };

const CAMPOS_NOME = ['consumidorPessoaNome', 'consumidorNome', 'pacienteNome', 'nomePaciente', 'nome'];
const CAMPOS_HORA = ['dataHoraInicio', 'horaInicio', 'dataInicio', 'inicio', 'horario', 'hora', 'dataHora', 'data'];

function hora(ag) {
  const v = primeiro(ag, CAMPOS_HORA);
  if (!v) return null;
  const m = String(v).match(/(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : null;
}
function iniciais(nome) {
  if (!nome) return '?';
  return String(nome).trim().split(/\s+/).filter(p => p.length > 2 || /^[A-ZÀ-Ý]/.test(p))
    .map(p => p[0].toUpperCase() + '.').join('');
}
function digitos(fone) { return String(fone ?? '').replace(/\D/g, ''); }
function ehCelular(fone) { const d = digitos(fone); return d.length === 11 && d[2] === '9'; }
function foneMascarado(fone) {
  const d = digitos(fone);
  if (d.length < 10) return 'sem telefone';
  return `(${d.slice(0, 2)}) ****-**${d.slice(-2)}`;
}
const ehAvaliacao = (ag) => semAcento(ag.tipoAtendimento).includes('avaliacao');

// 3) Contas
const porSituacao = {};
for (const ag of agendamentos) {
  const s = ag.situacao || '(sem situação)';
  porSituacao[s] = (porSituacao[s] || 0) + 1;
}
const semAvaliacao = agendamentos.filter(ag => !ehAvaliacao(ag));
const horarios = agendamentos.map(hora).filter(Boolean).sort();
const comCelular = agendamentos.filter(ag => ehCelular(ag.consumidorPessoaFone1)).length;

const ordenados = [...agendamentos].sort((a, b) => (hora(a) || '99').localeCompare(hora(b) || '99'));
const exemplos = ordenados.slice(0, 3).map(ag => ({
  paciente_iniciais: iniciais(primeiro(ag, CAMPOS_NOME)),
  horario: hora(ag) || '?',
  tipo: ag.tipoAtendimento || '?',
  telefone: foneMascarado(ag.consumidorPessoaFone1),
}));

return [{
  json: {
    data_consultada: amanha,
    status_http_agenda: statusHttp,
    total_agendamentos: agendamentos.length,
    total_por_situacao: porSituacao,
    total_sem_avaliacoes: semAvaliacao.length,
    total_avaliacoes: agendamentos.length - semAvaliacao.length,
    primeira_consulta: horarios[0] || null,
    com_celular_valido: comCelular,
    sem_celular_valido: agendamentos.length - comCelular,
    exemplos_mascarados: exemplos,
    // Só os NOMES dos campos (sem valores) para ajustarmos o fluxo, se preciso:
    campos_disponiveis: agendamentos[0] ? Object.keys(agendamentos[0]) : [],
  }
}];
