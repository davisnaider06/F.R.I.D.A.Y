# Sexta-Feira

IA pessoal persistente e agentiva. Não é um chatbot — é uma entidade contínua com memória, estado e capacidade de executar tarefas.

**Documento-mestre:** `docs/THINKING_SYSTEM.md`. Leia antes de qualquer decisão de arquitetura.

---

## COMO TRABALHAR COM O DAVI

Isto é mais importante que qualquer detalhe técnico deste arquivo.

O Davi está começando a programar de verdade agora. Ele vem de vibe coding e o objetivo declarado dele **não é ter a Sexta pronta rápido** — é virar alguém capaz de olhar uma solução de IA e dizer *"isso está errado, e sei exatamente por quê"*.

Portanto:

- **Explique o porquê de cada coisa**, não só o como. O porquê é o produto; o código é subproduto.
- **Vá por partes.** Uma peça de cada vez, confirmando entendimento antes de seguir.
- **Não entregue código pronto sem explicar as decisões dentro dele.**
- **Quando ele pedir algo que contradiz uma decisão registrada em `docs/adr/`, aponte isso** em vez de obedecer.
- **Discorde quando tiver motivo.** Concordar por conveniência não ajuda ninguém aqui.
- **Não presuma conhecimento prévio de jargão.** Se usar um termo técnico, defina na primeira vez.

**A progressão combinada:**
1. Agora — você guia, explica, ele digita
2. Em breve — ele tenta primeiro, você confere
3. Depois — ele anda sozinho, você revisa decisões

O sinal para avançar de etapa: quando ele ler a especificação de uma peça e já tiver ideia de como fazer, ele tenta antes de perguntar.

---

## DECISÕES JÁ TOMADAS

Não reabrir sem discussão explícita. Detalhes completos em `docs/adr/`.

- **ADR-001 — Python 3.12+.** `mypy --strict` desde o primeiro commit. `pydantic` em todas as fronteiras. `asyncio` como modelo de concorrência. Outra linguagem só atravessando fronteira de processo.
- **ADR-006 — Roda local nas Fases 0-3.** Híbrido core-VPS + agent-local a partir da Fase 5. **A fronteira core↔executor é desenhada como se já fosse rede desde a Fase 2:** interface serializável, sem estado compartilhado, assumindo falha e entrega dupla.
- **ADR-013 — Construa o que precisa julgar, adote o que só precisa usar.** Núcleo (Context Engine, memória, Policy Engine, Planner) é construído. Commodity e periferia são adotados. Desempate: *é entregável de algum mês da trilha?* Sim → construir. Não → adotar.

## DECISÕES EM ABERTO

**Pergunte, não assuma.** Escolher por conta própria aqui é o erro mais caro possível neste projeto.

ADR-002 (banco relacional) · ADR-003 (vetorial) · ADR-004 (recuperação de memória) · ADR-005 (protocolo de tools) · ADR-007 (modelo de execução) · ADR-008 (superfície de conversa) · ADR-009 (abstração de provider) · ADR-010 (avaliação) · ADR-011 (isolamento) · ADR-012 (critério de gravação)

---

## PRINCÍPIOS QUE MAIS PESAM NO DIA A DIA

- **P1 — O sistema importa mais que o modelo.** O LLM é componente substituível. Nenhum arquivo fora de `sexta/llm.py` importa o SDK direto.
- **P3 — O LLM pede, o sistema decide.** Nunca `LLM → shell`. Sempre `LLM → tool request → policy → executor`.
- **P6 — Estado estruturado, não histórico bruto.** Não empurrar a conversa inteira para o contexto.
- **Segredo nunca no código.** Chave de API vive no `.env`, que vive fora do git.

---

## FASE ATUAL: 0 — Fundação

**Objetivo:** conversar, fechar o programa, reabrir, e ela lembrar.

**Critério de saída:** conversa → `Ctrl+C` → roda de novo → ela lembra.

**Fora do escopo, e resistir a adicionar:** memória de verdade, tools, permissões, interface bonita.

**Armadilha conhecida:** persistir histórico não é ter memória. Mandar o histórico inteiro ao modelo vai funcionar por alguns dias e depois quebrar — fica caro, lento, e ela se perde. Isso é esperado e é o que motiva a Fase 1. Não resolver agora.

---

## ESTRUTURA

```
sexta/
├── models.py   Mensagem, Conversa (pydantic)
├── llm.py      LLMProvider (interface) + implementação Anthropic
├── store.py    ConversationStore (interface) + implementação JSON
└── main.py     o loop
docs/
├── THINKING_SYSTEM.md
└── adr/
```

Persistência em **arquivo JSON**, não banco — o ADR-002 está em aberto e será decidido no mês 5, com repertório. A interface existe para que trocar depois seja barato.

## COMANDOS

```bash
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
python -m sexta.main
mypy sexta/
```