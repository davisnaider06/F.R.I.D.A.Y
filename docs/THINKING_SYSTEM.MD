# TS — THINKING SYSTEM

**Dono:** Davi
**Projeto-mãe:** Sexta-Feira
**Versão:** 1.0 — 11/08/2026
**Status:** documento vivo. Toda decisão nova entra aqui antes de virar código.

---

## 0. O QUE É ESTE DOCUMENTO

Este é o contexto-mestre. Ele existe para que qualquer IA (Claude, GPT, Gemini, modelo local) possa ser instruída com uma única frase:

> "Leia `THINKING_SYSTEM.md`. A partir dele, vamos trabalhar."

E a partir daí ela saiba quem é o Davi, o que ele está construindo, por quê, sob quais princípios, com quais limites, e o que **já foi decidido** versus o que **ainda está em aberto**.

**Regra fundamental deste documento:** ele distingue explicitamente três coisas.

| Marcador | Significado |
|---|---|
| **DECIDIDO** | Já foi acordado. Não reabrir sem discussão explícita. |
| **EM ABERTO** | Ainda não foi decidido. A IA deve **perguntar**, não assumir. |
| **DIREÇÃO** | Intenção de longo prazo, sem compromisso de implementação. |

Se uma IA precisar de algo que este documento marca como **EM ABERTO**, ela deve parar e perguntar. Não deve escolher por conta própria e seguir em frente. Esse é o erro mais caro que pode acontecer neste projeto.

---

## 1. VISÃO

**DECIDIDO.**

Duas coisas, entrelaçadas:

**1. O objetivo humano.** Davi quer se tornar um builder/engenheiro extremamente competente, usando IA como multiplicador — não como muleta. Ele não quer abandonar o vibe coding; quer fazer vibe coding em um nível muito mais alto, porque entende engenharia o suficiente para comandar, questionar e revisar as IAs.

O teste de sucesso é este:

> Olhar uma solução que o Claude produziu e dizer *"isso está errado, e sei exatamente por quê"*.

Não é decorar APIs. Não é escrever manualmente cada linha. É ter o modelo mental para julgar.

**2. O objetivo técnico.** Construir a **Sexta-Feira**: uma IA pessoal persistente e agentiva. Não um chatbot. Uma segunda camada computacional sobre a vida digital do Davi.

As duas coisas são o mesmo projeto. A Sexta-Feira é o veículo do aprendizado; o aprendizado é o que torna a Sexta-Feira construível. Estudar sem construir vira teoria morta. Construir sem estudar vira dependência cega da IA.

---

## 2. FILOSOFIA E PRINCÍPIOS

**DECIDIDO.**

### P1. O sistema importa mais que o modelo

O objetivo **não** é construir a IA mais inteligente possível. É construir **o melhor sistema possível para aproveitar inteligências artificiais**.

Consequência direta: o LLM é um componente substituível. Trocar Claude → GPT → Gemini → modelo local não pode exigir reconstruir a Sexta. A inteligência é plugável; identidade, memória, contexto, políticas e execução são do sistema.

### P2. O LLM não é o cérebro inteiro

O LLM é a peça de **raciocínio**. O resto — memória, contexto, estado, ferramentas, percepção, planejamento, execução, políticas, observação, avaliação — é engenharia clássica em volta dele.

Quando algo falha, a primeira pergunta é: *"isso é um problema de raciocínio ou um problema de contexto?"* Na esmagadora maioria das vezes é contexto. Trocar de modelo raramente é a resposta.

### P3. O LLM pede, o sistema decide

Nunca:

```
LLM → shell irrestrito
```

Sempre:

```
LLM → Tool Request → Policy Engine → Permission → Executor → OS
```

O modelo **solicita** ações. O sistema **autoriza** e executa. Essa fronteira é inegociável e é a base de toda a segurança do projeto.

### P4. Continuidade sobre performance

Uma Sexta que responde em 400ms mas esquece tudo é pior que uma Sexta que responde em 3s e lembra de tudo. Latência é otimização; continuidade é identidade.

### P5. Autonomia é conquistada, não concedida

Autonomia é superfície de risco. Cada nível novo só é liberado depois que o nível anterior demonstrou confiabilidade observável. Não se começa no nível 3.

### P6. Estado estruturado > histórico bruto

Não empurrar todo o histórico da conversa para o contexto do LLM. Manter uma representação estruturada de estado, memória e decisões, e montar o contexto deliberadamente a cada turno.

### P7. Construir para quebrar

O ciclo de aprendizado é: aprender → implementar → aplicar na Sexta → quebrar → analisar → melhorar. Quebrar de propósito é parte do método, não acidente.

### P8. Davi é o arquiteto

O Claude é multiplicador, não dono. Decisões de arquitetura, trade-offs e prioridade são do Davi. Se o Claude tomar uma decisão arquitetural sozinha, isso é um bug do processo, não uma conveniência.

---

## 3. OBJETIVOS E NÃO-OBJETIVOS

**DECIDIDO.**

### Objetivos

- Entidade conversacional contínua, com identidade estável ao longo de meses e anos.
- Memória real: episódica, semântica e procedural.
- Consciência de estado: o que está acontecendo agora, o que ficou pendente, o que ela mesma fez.
- Execução de tarefas reais no mundo digital, via ferramentas com permissão.
- Modelo de permissões e políticas explícito e auditável.
- Autonomia progressiva em três níveis.
- Iniciativa proativa: falar sem ser chamada, quando faz sentido.
- Ser o laboratório onde cada tópico de estudo do Davi é aplicado.

### Não-objetivos

- **Não** é AGI. Não estamos criando inteligência do zero.
- **Não** é produto comercial (por enquanto). Multiusuário, billing, SLA, compliance: fora de escopo.
- **Não** é competir com ChatGPT/Claude como assistente genérico. A Sexta é pessoal e situada.
- **Não** é interface bonita primeiro. Voz, visão, gestos e holograma são periferia, não centro. A armadilha clássica é construir a interface do JARVIS antes do cérebro do JARVIS.
- **Não** é substituir o julgamento do Davi. É amplificá-lo.

---

## 4. MODELO DE INTERAÇÃO

**DECIDIDO.**

### O que a Sexta NÃO é

```
Você: faça X
IA:   feito.
```

Requisições independentes. Sem estado. Sem continuidade. Cada frase tratada como uma pergunta isolada.

### O que a Sexta É

```
Você:  Sexta, lembra daquele projeto?
Sexta: Lembro. Você estava na arquitetura de creators e sellers.
       A última decisão foi separar os dois perfis na mesma plataforma.
       Quer continuar daquele ponto?

Você:  Isso. Quero adicionar afiliados.
Sexta: Isso afeta comissão, tracking e checkout. Sugiro começar pelo
       modelo de dados. Quero analisar a arquitetura atual?

Você:  Pode.
       [ela lê repo, banco, docs, git]
Sexta: Três pontos precisam mudar. O principal: a venda hoje está
       vinculada direto ao seller. Para afiliados precisamos de uma
       relação entre order, creator e commission.

Você:  Resolve.
       [ela trabalha]
Sexta: Terminei. Branch criada, schema alterado, tracking implementado,
       testes adicionados. Dois testes antigos quebraram por dependerem
       do relacionamento anterior — corrigi ambos. Não fiz merge.

Você:  Abre o PR.
```

### O ciclo

```
conversa → entendimento → contexto → decisão → execução → feedback → conversa
```

E a conversa **continua durante a execução**. Não é um bloqueio.

### Propriedades exigidas

- **Referência implícita.** "aquele projeto", "aquele bug de ontem", "aquilo que discutimos" precisam resolver. Sem obrigar o Davi a fornecer IDs, paths e branches.
- **Troca de assunto e retorno.** Falar de endpoint → agendar algo → voltar ao endpoint. O contexto anterior tem que sobreviver.
- **Cada mensagem modifica estado.** A conversa é a interface de escrita do estado da tarefa, não só um log.
- **Perguntas de desambiguação.** Quando o objetivo é vago, a Sexta pergunta antes de agir — não chuta.

---

## 5. ARQUITETURA COGNITIVA

**DECIDIDO** no nível conceitual. **EM ABERTO** no nível de implementação.

### O loop

```
perceber → compreender → lembrar → raciocinar → planejar → agir
    → observar resultado → atualizar estado → continuar
```

### O diagrama de alto nível

```
                         SEXTA-FEIRA
                              │
                    ┌─────────▼─────────┐
                    │   CONVERSATION    │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  CONTEXT ENGINE   │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          MEMORY           POLICIES        WORLD STATE
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                         REASONING LLM
                              │
                              ▼
                           PLANNER
                              │
                              ▼
                            TASKS
                              │
                              ▼
                           EXECUTOR
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
           TOOLS            AGENTS           EVENTS
             │                │                │
             ▼                ▼                ▼
          Computer          Coding           Sensors
          Browser           Claude           Webhooks
          Files             Codex            Scheduler
          Git               Gemini
          APIs
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                           RESULTS
                              │
                              ▼
                           MEMORY
                              │
                              ▼
                        CONVERSATION
```

### O componente mais importante: CONTEXT ENGINE

É ele que decide, a cada turno, **o que o LLM vai ver**. Recebe:

- a mensagem atual
- o estado da conversa
- memórias recuperadas (episódica, semântica, procedural)
- estado do mundo
- políticas ativas
- resultados de ferramentas recentes

E produz um contexto montado deliberadamente. Este é o componente que decide se a Sexta parece uma entidade ou um chatbot com histórico. É onde vale gastar a maior parte do esforço de engenharia.

---

## 6. MEMÓRIA

**DECIDIDO** na taxonomia. **EM ABERTO** na implementação.

### Os três tipos

```
MEMORY
│
├── Episodic    → acontecimentos, com tempo
│   "Ontem decidimos usar PostgreSQL."
│
├── Semantic    → fatos e conhecimento estável
│   "O projeto Sexta-Feira usa PostgreSQL."
│
└── Procedural  → procedimentos e habilidades
    "O deploy da Sexta segue este processo: ..."
```

### Princípios de memória

- **Escrita seletiva.** Nem tudo vira memória. Precisa haver um critério de gravação, senão a memória vira um dump inútil.
- **Recuperação híbrida.** Similaridade vetorial sozinha não basta — favorece documentos antigos e ignora recência e relevância estrutural. A direção é combinar embedding + full-text + recência + relacionamento explícito.
- **Esquecimento é feature.** Memória que só cresce degrada. Precisa haver consolidação e decaimento.
- **Decisões e preferências NÃO ficam só na memória do LLM.** Viram dados estruturados. Ver §10.
- **Memória de relacionamento.** A Sexta lembra de acordos: "não faça merge automaticamente", dito uma vez, vale três meses depois — e ela cita o motivo quando aplica.

Exemplo do comportamento esperado:

> **Davi (hoje):** Sexta, não quero que você faça merge automaticamente.
>
> **Davi (3 meses depois):** Implementa essa task.
>
> **Sexta:** Vou criar a branch e preparar o PR, mas não vou fazer merge, conforme sua política atual.

### EM ABERTO

- Banco vetorial, banco relacional, estratégia de embedding
- Critério de gravação (heurística? LLM decide? híbrido?)
- Algoritmo de consolidação e decaimento
- Como versionar memória quando uma decisão antiga é revogada

---

## 7. ESTADO E WORLD MODEL

**DECIDIDO** no conceito.

### Conversation state

O LLM recebe uma **representação** do estado, não o histórico bruto.

```json
{
  "goal": "melhorar memória",
  "project": "sexta-feira",
  "repository": "sexta-feira",
  "task": "hybrid ranking",
  "branch": "feature/memory-hybrid-ranking",
  "status": "implementing",
  "decisions": [
    "usar embedding + full-text",
    "considerar recência",
    "não alterar produção diretamente"
  ],
  "pending_questions": [],
  "recent_tool_results": []
}
```

### World state — DIREÇÃO

```
WORLD STATE

User:              Davi
Environment:       Home
Devices:           PC, Phone
Applications:      VS Code, Chrome
Projects:          Sexta-Feira, Atlas, ...
Current activity:  Coding
Current task:      AI architecture
```

Isso permite que ela raciocine considerando o estado real do mundo digital, não só o texto da conversa. É de longo prazo — não é do primeiro ciclo.

---

## 8. FERRAMENTAS (TOOLS)

**DECIDIDO** no modelo. **EM ABERTO** no protocolo e no inventário final.

### O fluxo

```
LLM → Tool Request → Permission / Policy → Executor → Resultado → LLM
```

### Inventário previsto

```
tools/
├── computer/     wake_pc, lock_pc, shutdown_pc
├── git/          clone, checkout, branch, commit, push
├── github/       issues, PRs, reviews
├── coding/       inspect_repo, run_tests, run_agent
├── browser/
├── filesystem/
├── terminal/
├── database/
├── calendar/
├── email/
├── cloud/
└── communication/
```

Cada tool carrega:

- schema de entrada e saída
- classe de permissão
- se é destrutiva
- se é reversível
- custo/latência esperados

### Sobre "liga meu PC"

O exemplo original — *"Sexta, liga meu PC e implementa a task X no repo Z"* — era **ilustração do nível de autonomia desejado**, não requisito prioritário. Tecnicamente é resolvível com Wake-on-LAN (magic packet, exige BIOS/UEFI e placa configurados) seguido de agent local:

```
check status → offline? → Wake-on-LAN → wait → ping → SSH/agent → ready
```

Fica registrado como possível, mas **não é prioridade**. O que importa do exemplo é a cadeia: intenção falada → decomposição → execução real → relato de volta na conversa.

---

## 9. AGENTS

**DIREÇÃO.**

A Sexta orquestra outros agentes especializados em vez de tentar fazer tudo com um único modelo:

- **Coding agents** (Claude Code, Codex, outros) para implementação
- **Research agents** para investigação
- **Review agents** para revisão de diff

A Sexta é a **coordenadora**: entende o objetivo, monta contexto, delega, avalia o resultado, e reporta. Ela não precisa ser boa em tudo — precisa ser boa em saber quem chamar e em julgar o que voltou.

Exemplo de decomposição para *"implementa a task #142"*:

```
get_task(142) → inspect_repository() → create_branch()
→ run_coding_agent() → run_tests() → review_diff() → report_result()
```

---

## 10. PERMISSÕES E POLÍTICAS

**DECIDIDO.** Esta é a seção mais crítica do documento.

### Política como dado, não como prompt

Políticas **não** dependem da memória do LLM. São configuração estruturada, versionada e auditável.

```
user_policy

auto_merge                        = false
auto_deploy                       = false
allow_shell                       = true
allow_delete                      = false
require_confirmation_destructive  = true
```

### Regras

- Toda ação passa pelo Policy Engine antes de executar. Sem exceção.
- Ação destrutiva sem política explícita = **negada por padrão**.
- Toda execução é registrada: o que foi pedido, o que foi autorizado, o que rodou, o que resultou.
- Quando a Sexta esbarra num limite, ela **relata e pede** — não contorna:

> "Encontrei um problema de infraestrutura que exige alteração de firewall. Não tenho permissão para isso. Quer que eu execute?"

- O LLM pode ser induzido a erro (conteúdo malicioso em issue, README, página web). O Policy Engine é a última linha de defesa e **não** confia na intenção do modelo.

---

## 11. NÍVEIS DE AUTONOMIA

**DECIDIDO.**

### Nível 1 — Assistido

Ela propõe, você confirma cada execução.

> "Vou criar a branch e alterar 4 arquivos. Posso continuar?"

### Nível 2 — Autônomo controlado

Você autoriza **classes** de ação antecipadamente.

> "Pode implementar tasks do repositório Sexta-Feira sem confirmar, mas não faça merge."

```
create branch → code → test → review → report
```

### Nível 3 — Autônomo por objetivo

Você fornece um objetivo; ela identifica as tarefas.

> "Cuide das tasks de baixa prioridade do projeto."

```
find tasks → prioritize → plan → implement → test → review → PR → notify
```

**Regra:** não chegar ao nível 3 cedo. Cada nível só é liberado depois que o anterior provou confiabilidade em uso real, com log auditável.

---

## 12. INICIATIVA PROATIVA

**DIREÇÃO.**

A Sexta não deve apenas esperar comando.

> **08:00 — Sexta:** Bom dia. Analisei seus projetos. A task #142 continua bloqueando o módulo de memória. O deploy da Atlas está estável. Você tem reunião às 14h. Recomendo priorizar a #142 antes do meio-dia.

Exige: `Scheduler + Memory + Calendar + Integrações de projeto + Task system + Reasoning`.

Regra de bom senso: iniciativa só vale se tiver alto sinal. Uma Sexta que fala demais vira notificação ignorada — e uma notificação ignorada é pior que silêncio.

---

## 13. PERCEPÇÃO — VOZ, VISÃO, GESTOS

**DIREÇÃO. Explicitamente adiado.**

```
Voz:    Speech → STT → Sexta → TTS
Visão:  Camera → Vision Model → objetos/pessoas/gestos/cena → Sexta
```

Princípio de projeto: **não mandar pixels crus para o LLM.** Modelos de percepção convertem sinal em **eventos estruturados**:

```json
{ "event": "HAND_PINCH", "confidence": 0.94 }
```

Percepção é interface. O centro continua sendo conversa, memória, contexto, raciocínio, planejamento, ferramentas, execução e observação. **Não construir isso antes do cérebro existir.**

---

## 14. DECISÕES EM ABERTO (ADRs PENDENTES)

**Nenhuma destas foi decidida. A IA deve perguntar, não assumir.**

| # | Decisão | Notas |
|---|---|---|
| ADR-001 | Linguagem principal do core | Trade-off: ecossistema de IA (Python) vs. tipagem/concorrência/robustez |
| ADR-002 | Banco relacional | Estado, tarefas, políticas, log de auditoria |
| ADR-003 | Armazenamento vetorial | Extensão do relacional vs. serviço dedicado |
| ADR-004 | Estratégia de recuperação de memória | Híbrido: vetor + full-text + recência + grafo? |
| ADR-005 | Protocolo de tools | MCP, function calling nativo, ou camada própria |
| ADR-006 | Onde a Sexta roda | Local, servidor pessoal, cloud, ou híbrido |
| ADR-007 | Modelo de execução | Processo único, fila + workers, event-driven |
| ADR-008 | Superfície de conversa | CLI, web, mobile, voz — e em que ordem |
| ADR-009 | Provider de LLM e abstração | Como garantir substituibilidade real (P1) |
| ADR-010 | Estratégia de avaliação | Como medir se a Sexta está ficando melhor |
| ADR-011 | Isolamento de execução | Container, VM, sandbox — para tools perigosas |
| ADR-012 | Critério de gravação de memória | Heurística, LLM, ou híbrido |

Cada uma vira um arquivo `ADR-XXX.md` quando for decidida: contexto, opções consideradas, decisão, consequências, data.

---

## 15. ROADMAP DE DESENVOLVIMENTO

**DECIDIDO** na ordem. **EM ABERTO** nos prazos.

A ordem é deliberada. Cada fase só existe porque a anterior existe.

### Fase 0 — Fundação
Loop de conversa funcionando. Um provider de LLM atrás de uma abstração. Persistência de conversa. Nada de tools ainda.
**Critério de saída:** conversar com a Sexta, fechar, reabrir e ela lembrar do que foi dito.

### Fase 1 — Memória
Os três tipos de memória. Gravação seletiva. Recuperação. Context Engine v1.
**Critério de saída:** "lembra daquele projeto?" funciona sem você dar nenhum identificador.

### Fase 2 — Tools + Permissões
Camada de tools com schema. Policy Engine. Log de auditoria. Nível de autonomia 1.
**Critério de saída:** ela executa uma ação real no mundo, pede confirmação, e o log registra tudo.

### Fase 3 — Execução de tarefas
Git, GitHub, repositório. Planner. Delegação a coding agent. Testes e review de diff.
**Critério de saída:** "implementa a task #X" produz uma branch com código e testes passando.

### Fase 4 — Estado e continuidade
Conversation state estruturado. Troca de assunto e retorno. Referência implícita robusta. Nível de autonomia 2.
**Critério de saída:** três assuntos entrelaçados na mesma conversa sem ela se perder.

### Fase 5 — Proatividade
Scheduler. Integração com calendário e projetos. Briefing matinal. Detecção de bloqueios.
**Critério de saída:** ela fala primeiro, e o que ela fala é útil.

### Fase 6 — Percepção
Voz (STT/TTS). Visão. Eventos estruturados.
**Critério de saída:** conversar com ela por voz sem degradar nada do que já funciona.

### Fase 7 — Autonomia por objetivo
Nível 3, dentro de escopo restrito e com política apertada.

---

## 16. TRILHA DE ESTUDOS — 12 MESES

**DECIDIDO** na estrutura.

### O método

```
Aprender → Implementar o conceito isolado → Aplicar na Sexta
    → Quebrar de propósito → Analisar → Melhorar
```

Nada é estudado no vácuo. Todo mês tem **um entregável verificável dentro da Sexta**. Se um mês não produziu código que ficou no projeto, o mês falhou.

**Regra de honestidade:** o Claude pode escrever o código. O Davi precisa conseguir **explicar cada decisão do código** sem olhar. O teste é oral, não visual. Se você não consegue explicar por que aquela estrutura de dados e não outra, você não aprendeu — você copiou.

---

### MÊS 1 — Fundamentos de Computação

**Estudo:** representação binária, memória, ponteiros e referências, stack vs. heap, o que um processo realmente é, como um programa vira instruções. Compilado vs. interpretado. O que o runtime da sua linguagem faz por você.

**Por que importa:** sem isso, toda discussão de performance vira superstição. Você não vai saber por que uma estrutura é lenta, só que ela é.

**Entregável na Sexta:** loop de conversa mínimo, rodando, com persistência em arquivo. Sem framework. Você tem que entender cada linha.

**Teste de compreensão:** explicar o que acontece na memória quando você carrega o histórico de uma conversa longa.

---

### MÊS 2 — Estruturas de Dados e Algoritmos

**Estudo:** arrays, hash maps, árvores, grafos, heaps. Complexidade assintótica de verdade — não decorar tabela, entender de onde vem. Ordenação e busca. Quando O(n²) é aceitável e quando não é.

**Por que importa:** memória e recuperação são, no fundo, problemas de estrutura de dados. Ranking é ordenação com critério composto. Grafo de relacionamento entre memórias é grafo.

**Entregável na Sexta:** busca em memória por palavra-chave, implementada à mão. Índice invertido simples. Medir o tempo com 100, 10.000 e 1.000.000 de entradas e explicar a curva.

**Quebrar de propósito:** rodar busca linear em 1M de entradas e sentir a dor. Depois indexar.

---

### MÊS 3 — Sistemas Operacionais

**Estudo:** processos e threads, concorrência vs. paralelismo, escalonamento, I/O bloqueante e não-bloqueante, sistema de arquivos, permissões, sinais, IPC. O que é um syscall.

**Por que importa:** a Sexta vai executar processos, rodar agentes em paralelo, mexer em arquivos e precisar de isolamento. Sem isso você não consegue nem raciocinar sobre a camada de execução.

**Entregável na Sexta:** Executor v0 — capaz de rodar um processo externo, capturar stdout/stderr, aplicar timeout e matar o processo se travar.

**Quebrar de propósito:** rodar um comando que trava. Um que consome toda a memória. Um que escreve infinito no stdout. Cada um vai te ensinar algo diferente.

---

### MÊS 4 — Redes

**Estudo:** TCP/IP, DNS, HTTP/HTTPS, TLS, WebSockets, latência vs. throughput, retry, backoff, timeout, idempotência. Wake-on-LAN cabe aqui como curiosidade aplicada.

**Por que importa:** tudo na Sexta é chamada de rede. LLM, GitHub, calendário, agentes. Rede falha o tempo todo, e sistemas que não assumem isso quebram feio.

**Entregável na Sexta:** camada de cliente HTTP com retry, backoff exponencial, timeout e tratamento de erro por classe. Toda chamada externa passa por ela.

**Quebrar de propósito:** simular API lenta, API que devolve 500, API que corta a conexão no meio da resposta.

---

### MÊS 5 — Bancos de Dados

**Estudo:** modelo relacional, normalização e quando desnormalizar, índices (e por que um índice acelera leitura e desacelera escrita), transações, ACID, níveis de isolamento, plano de execução. Depois: quando SQL não serve e o que a alternativa custa.

**Por que importa:** memória, estado, políticas, tarefas e auditoria vivem em banco. Modelo de dados ruim aqui envenena o projeto inteiro.

**Entregável na Sexta:** schema real — conversas, mensagens, memórias, tarefas, políticas, log de auditoria. Migrations. Índices justificados um por um.

**Decisão a tomar:** ADR-002.

**Teste de compreensão:** ler o plano de execução da sua query mais pesada e explicar cada etapa.

---

### MÊS 6 — Fundamentos de Machine Learning

**Estudo:** aprendizado supervisionado e não-supervisionado, features, treino/validação/teste, overfitting, métricas (precisão, recall, F1 — e por que acurácia engana). Espaços vetoriais e similaridade por cosseno.

**Por que importa:** é a base de embeddings e de qualquer avaliação séria. E é o que te permite dizer "esse benchmark não significa o que você acha que significa".

**Entregável na Sexta:** conjunto de avaliação da memória — 50 perguntas com respostas esperadas, medindo se a recuperação traz a memória certa. Precisão e recall reais.

---

### MÊS 7 — Deep Learning

**Estudo:** redes neurais, backpropagation, gradiente descendente, funções de ativação, embeddings, regularização. Você não precisa treinar modelos grandes — precisa entender o que está acontecendo.

**Por que importa:** desmistifica o LLM. Você para de tratar o modelo como mágica e começa a tratar como sistema com propriedades conhecidas e limitações previsíveis.

**Entregável na Sexta:** pipeline de embeddings — gerar, armazenar, versionar. Busca semântica funcionando ao lado da busca por palavra-chave do mês 2.

**Quebrar de propósito:** casos onde a busca semântica falha e a lexical acerta. Isso motiva o híbrido do mês 9.

---

### MÊS 8 — Transformers e LLMs

**Estudo:** atenção, tokenização, janela de contexto, decodificação e sampling, temperatura, por que alucinação acontece estruturalmente. Prompt como programa. Custo por token.

**Por que importa:** é o motor da Sexta. Sem entender a janela de contexto você não consegue projetar o Context Engine.

**Entregável na Sexta:** Context Engine v1 — montagem deliberada de contexto, com orçamento de tokens explícito e política de priorização quando não cabe tudo.

**Teste de compreensão:** explicar exatamente o que entra no contexto num turno específico e por quê cada pedaço ganhou espaço.

---

### MÊS 9 — RAG e Memória

**Estudo:** chunking, estratégias de recuperação, reranking, busca híbrida, avaliação de RAG. Consolidação e esquecimento. Modelagem de memória episódica vs. semântica vs. procedural.

**Por que importa:** este é o coração da Sexta. É o que faz ela parecer uma entidade em vez de um chatbot.

**Entregável na Sexta:** sistema de memória completo — três tipos, gravação seletiva, recuperação híbrida (vetor + full-text + recência), reranking. Avaliado com o conjunto do mês 6.

**Meta mensurável:** superar a baseline puramente vetorial no seu próprio conjunto de avaliação. Com número.

**Decisões a tomar:** ADR-003, ADR-004, ADR-012.

---

### MÊS 10 — Agentes

**Estudo:** loop tool-use, planejamento, decomposição de tarefas, ReAct e variantes, tratamento de erro em agentes, multi-agente, avaliação de agente. Modos de falha: loop infinito, alucinação de ferramenta, execução parcial.

**Por que importa:** é a camada que transforma conversa em execução.

**Entregável na Sexta:** Planner + Executor + camada de tools com Policy Engine. Nível de autonomia 1 funcionando ponta a ponta. A Sexta implementa uma task real num repositório real.

**Decisões a tomar:** ADR-005, ADR-011.

**Quebrar de propósito:** tentar prompt injection na sua própria Sexta — via issue do GitHub, via README, via conteúdo de página. Se o Policy Engine falhar, você acabou de aprender a lição mais importante do ano.

---

### MÊS 11 — Sistemas Distribuídos

**Estudo:** teorema CAP, consistência eventual, filas e mensageria, idempotência, entrega at-least-once vs. exactly-once, tolerância a falha, observabilidade (logs, métricas, traces).

**Por que importa:** quando a Sexta roda tarefas longas, em paralelo, com agentes externos e proatividade agendada, ela **é** um sistema distribuído — quer você tenha planejado ou não.

**Entregável na Sexta:** execução assíncrona com fila, tarefas retomáveis, tracing de ponta a ponta de uma execução, dashboard de observabilidade.

**Decisões a tomar:** ADR-007.

**Quebrar de propósito:** matar o processo no meio de uma tarefa de 20 minutos. Ela tem que retomar ou falhar limpo — nunca ficar num estado inconsistente.

---

### MÊS 12 — Arquitetura de Sistemas e Consolidação

**Estudo:** design de sistemas de verdade, trade-offs, limites de módulo, acoplamento e coesão, evolutividade, ADRs, revisão de segurança, análise de custo.

**Por que importa:** é onde tudo junta. E é a habilidade mais valiosa da lista — a que separa quem escreve código de quem projeta sistemas.

**Entregável na Sexta:** refatoração arquitetural completa do que foi construído. Todos os ADRs escritos. Revisão de segurança inteira. Documentação do sistema real, não do sistema imaginado.

**Teste final:** trocar o provider de LLM inteiro. Se doer muito, o P1 falhou e você aprendeu por quê — que também é um resultado válido.

---

### EM PARALELO — o ano inteiro

**História, filosofia, política, economia.**

Não é enfeite. Engenharia é decisão sob incerteza com informação incompleta, e isso é um problema epistemológico antes de ser técnico. Filosofia dá rigor argumentativo. História dá padrões de como sistemas complexos falham. Economia dá modelo de incentivo e custo de oportunidade. Política dá modelo de poder e coordenação.

Concretamente: isso é o que te permite discordar do Claude com argumento estruturado, em vez de intuição.

**Ritmo sugerido:** leitura contínua, sem entregável. Isso é lastro, não sprint.

---

### Regras da trilha

1. **Nenhum mês sem código que ficou.** Estudo sem artefato não conta.
2. **O Claude pode escrever, você tem que conseguir explicar.** Sem olhar.
3. **Quebrar é parte do currículo.** Cada mês tem um "quebrar de propósito" por design.
4. **Meses vão estourar.** Ajuste o escopo, não pule o mês. Melhor mês 9 bem feito em seis semanas que dois meses mal feitos.
5. **Revisão trimestral.** A cada três meses, reler este documento e atualizá-lo com o que a realidade ensinou.

---

## 17. COMO USAR O CLAUDE

**DECIDIDO.**

```
                    VOCÊ
                     │
             DECISÃO / OBJETIVO
                     │
                     ▼
                   CLAUDE
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Research    Architecture   Coding
        │            │            │
        └────────────┼────────────┘
                     ▼
                  REVIEW
                     │
                     ▼
                   VOCÊ
```

### Protocolo de trabalho

**Abertura de sessão:**
> "Leia `THINKING_SYSTEM.md`. A partir dele, vamos trabalhar em [X]."

**O que o Claude DEVE fazer:**
- Perguntar quando o documento marca algo como **EM ABERTO**
- Apresentar trade-offs antes de propor solução
- Explicar o *porquê*, não só o *como* — o objetivo do Davi é aprender
- Apontar quando o Davi está pedindo algo que contradiz uma decisão registrada aqui
- Discordar quando tiver razão para discordar

**O que o Claude NÃO deve fazer:**
- Escolher stack, banco ou framework por conta própria
- Assumir decisões de arquitetura sem registrar como ADR
- Otimizar prematuramente
- Entregar código sem explicar as decisões
- Concordar por conveniência

**Ao final de qualquer decisão relevante:** ela vira ADR e é adicionada a este documento. O documento é a fonte de verdade, não o histórico de conversa.

---

## 18. SEGURANÇA

**DECIDIDO.**

- **Padrão é negar.** Toda ação nova nasce sem permissão.
- **Ação destrutiva sempre confirma**, até no nível 3 de autonomia.
- **Segredos nunca no contexto do LLM.** Nem chaves, nem tokens, nem credenciais.
- **Isolamento de execução** para tudo que roda código arbitrário.
- **Prompt injection é ameaça real.** Conteúdo de issue, README, e-mail e página web é entrada não-confiável. O Policy Engine não confia na intenção do modelo.
- **Log de auditoria imutável.** Toda ação: pedida, autorizada, executada, resultado.
- **Reversibilidade.** Preferir sempre a ação desfazível: branch em vez de commit direto, PR em vez de merge, cópia em vez de sobrescrita.

---

## 19. AVALIAÇÃO

**EM ABERTO** na metodologia, **DECIDIDO** na necessidade.

Sem avaliação, "melhorou" vira sensação. Mínimo necessário:

- **Memória:** conjunto de perguntas com respostas esperadas; precisão e recall medidos.
- **Agente:** taxa de conclusão de tarefas, taxa de intervenção humana, taxa de erro.
- **Conversa:** o teste da referência implícita — quantas vezes o Davi precisou repetir contexto que ela deveria saber.
- **Segurança:** tentativas de injection bloqueadas / total de tentativas.

Regra: **antes de otimizar qualquer coisa, medir.** Depois otimizar. Depois medir de novo.

---

## 20. GLOSSÁRIO

| Termo | Significado |
|---|---|
| **Sexta-Feira** | A IA pessoal. O sistema. |
| **TS / Thinking System** | Este documento e o método que ele descreve. |
| **Context Engine** | Componente que monta o que o LLM vê a cada turno. |
| **Policy Engine** | Componente que autoriza ou nega ações. |
| **Tool** | Ação executável, com schema e classe de permissão. |
| **Agent** | Sistema externo especializado que a Sexta orquestra. |
| **ADR** | Architecture Decision Record — decisão registrada com contexto e consequências. |

---

## HISTÓRICO DE VERSÕES

| Versão | Data | Mudança |
|---|---|---|
| 1.0 | 11/08/2026 | Consolidação inicial da visão, arquitetura, princípios e trilha de 12 meses. |