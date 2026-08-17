# ADR-013 — Construir vs. adotar base existente

**Status:** DECIDIDO
**Data:** 17/08/2026
**Decisor:** Davi
**Relacionado:** ADR-001 (linguagem), ADR-005 (protocolo de tools), ADR-006 (onde roda), §1, §10, §18

---

## Contexto

A pergunta chegou pelo **OpenClaw** — assistente pessoal open-source (MIT), do Peter Steinberger, com tração enorme no GitHub. Self-hosted, model-agnostic, 20+ canais de mensagem, 50+ integrações, 100+ AgentSkills que executam shell, mexem em arquivos e fazem automação web. Cron, webhooks, GitHub.

A proposta era usá-lo como base e evoluir a partir dele, "matando grande parte do trabalho de início".

**Mas essa pergunta não é sobre o OpenClaw.** Ela vai voltar toda vez que aparecer um projeto novo e maduro — e vai aparecer, várias vezes, ao longo de 12 meses. Este ADR existe para responder a categoria, não o caso.

---

## O conflito real

O TS tem **dois** objetivos (§1), e eles puxam para lados opostos aqui:

1. Construir a Sexta-Feira.
2. Davi virar alguém capaz de julgar uma solução de IA e dizer por que está errada.

Adotar uma base madura acelera muito o objetivo 1 e pode zerar o objetivo 2 nas áreas adotadas. Construir tudo do zero serve o objetivo 2 e pode matar o objetivo 1 por exaustão.

Nenhum dos extremos está certo. O que faltava era um critério.

---

## O critério

> **Construa o que você precisa julgar. Adote o que você só precisa usar.**

Com um desempate operacional para os casos ambíguos:

> **Isso é entregável de algum mês da trilha (§23)?**
> Se sim → construir. Se não → adotar.

O segundo teste é mecânico de propósito. Ele existe para impedir a racionalização — que sempre vem no formato "esse componente específico é diferente, aqui vale adotar".

---

## Classificação dos componentes da Sexta

### CONSTRUIR — núcleo

Definem a identidade da Sexta **e** são alvo direto de aprendizado.

| Componente | Mês | Por quê |
|---|---|---|
| Context Engine | M8 | Decide o que o LLM vê. É o que separa entidade de chatbot com histórico. |
| Memória — três tipos, gravação seletiva, recuperação híbrida | M9 | O mês mais importante do ano. Adotar aqui é pular o M9. |
| Policy Engine e modelo de permissões | M10 | Última linha de defesa (§18). Não delegável, por definição. |
| Planner e decomposição de tarefas | M10 | — |
| Conversation state | Fase 4 | — |
| Fronteira core↔executor | Fase 2 | Já decidida no ADR-006. |
| Camada de resiliência de rede (retry, backoff, timeout) | M4 | É entregável do mês. |

### ADOTAR — commodity

Problema resolvido, e resolvê-lo de novo não ensina nada do que está na trilha.

- SDK de LLM (o protocolo, não a resiliência em volta dele)
- Modelo de embedding — gerar, nunca treinar
- Banco de dados e busca full-text
- STT / TTS
- Protocolo de tools, se o ADR-005 apontar para MCP
- Bibliotecas de tipagem e validação (`mypy`, `pydantic` — já no ADR-001)

### ADOTAR — periferia

Caro de construir, quase zero de aprendizado relevante. É onde o OpenClaw brilha.

- Canais de mensagem: WhatsApp, Telegram, Discord, Slack
- Conectores e integrações de terceiros
- Agendamento e webhooks (a menos que o ADR-007 diga o contrário)

Isso é coerente com o §13: interface e percepção são periferia, não centro.

---

## Decisão sobre o OpenClaw

**Terceira via: objeto de estudo e periferia. Não fundação.**

### 1. Case study no M10

Ler o código-fonte dele durante o mês de agentes. É provavelmente o melhor exemplo disponível de sistema de agentes real, com 100+ tools rodando em produção e uso de verdade.

Ler um sistema que funciona é aprendizado de altíssimo valor — e dá base para julgar decisões que você vai ter que tomar semanas depois. Fica registrado como recurso oficial do M10.

**O que procurar especificamente na leitura:**
- Como ele monta contexto
- Como (e se) ele limita o que o agente pode executar
- Como ele lida com falha de tool e execução parcial
- Onde a arquitetura dele diverge da sua, e se a divergência foi escolha ou acidente

### 2. Possível adaptador de canal depois

O ADR-006 já decidiu que a fronteira core↔executor é serializável e assume rede. Um adaptador de canal do outro lado dessa fronteira encaixa exatamente no formato previsto: **o core continua sendo o cérebro, o OpenClaw vira braço.**

Não antes da Fase 5. Não como dependência do core.

### 3. Não adotar como base do core

Três razões, em ordem de peso:

**a) Colide com o P3, estruturalmente.** Os relatórios de segurança descrevem instâncias rodando com shell irrestrito, permissões amplas de filesystem e tokens persistentes — código não-confiável e instruções não-confiáveis no mesmo loop, com credenciais válidas. Isso é exatamente o desenho que o P3 proíbe. E não se parafusa um Policy Engine num sistema cuja premissa é que o agente executa direto: isso não é plugin, é reescrita.

**b) O benefício e a mitigação se cancelam.** A mitigação recomendada — container isolado, sem credenciais que você não possa perder — remove justamente o que fazia ele valer a pena, que eram as integrações. Pesquisadores já demonstraram prompt injection fazendo instâncias expostas encaminharem e-mails privados para fora.

**c) O "início" que ele mata já era barato.** A Fase 0 é uma semana. As Fases 1 e 2 são o M9 e o M10 — os dois meses mais importantes da trilha. O que ele mata de graça é a Fase 0; o que ele mataria de caro é o ano.

---

## O argumento contrário, registrado

Não foi ignorado, foi pesado.

A maior causa de morte de plano de 12 meses não é dificuldade técnica — é perder a motivação no mês 3 sem nada funcionando. Uma Sexta respondendo no Telegram na semana 2 é antídoto real contra isso.

**Este argumento continua válido** e deve ser reaberto se a aderência despencar. A mitigação preferida, porém, é outra: entregar valor cedo com o próprio core (Fase 0 é uma semana), não importar uma base inteira.

---

## Regras que passam a valer

1. **Adotar não é neutro.** Quem adota herda as decisões arquiteturais do outro. Sempre verificar colisão com ADR-001 (linguagem) e ADR-006 (fronteira) **antes** de avaliar features.
2. **Nunca dois sistemas de permissão concorrentes.** Qualquer componente adotado que execute código ou toque credenciais passa pelo *seu* Policy Engine, mesmo que traga o próprio. Dois modelos de permissão em paralelo significa que nenhum dos dois é a última linha de defesa.
3. **Dependência adotada no núcleo exige ADR.** Na periferia, não exige.
4. **Ler código de sistema maduro é atividade de estudo legítima** e conta como bloco de teoria na rotina (§25).

---

## Consequências

**Positivas**
- A pergunta "e se eu usasse o projeto X?" agora tem resposta em dois minutos, não em meio dia de dúvida.
- M9 e M10 preservados como aprendizado real.
- O OpenClaw vira ganho (case study + canal futuro) em vez de escolha binária.

**Negativas, aceitas conscientemente**
- A Sexta demora mais para ter canais e integrações ricas. Até a Fase 5, a superfície de conversa será modesta.
- Existe risco de o critério ser usado para racionalizar construir tudo. O desempate mecânico ("é entregável de algum mês?") é a defesa contra isso — se a resposta for não e você ainda quiser construir, é vaidade, não engenharia.

---

## Quando revisitar

- **Reabrir a decisão sobre o OpenClaw como base** apenas se a aderência à rotina cair abaixo de 50% por dois meses e o diagnóstico for falta de artefato vivo — não cansaço, que tem outra solução (§31).
- **Revisar a classificação de componentes** a cada revisão trimestral (§27). Coisa que era núcleo pode virar commodity quando o aprendizado dela já foi extraído.
- **Não reabrir** por entusiasmo com projeto novo. É exatamente para isso que este ADR existe.