# ADR-001 — Linguagem principal do core

**Status:** DECIDIDO
**Data:** 14/08/2026
**Decisor:** Davi
**Relacionado:** ADR-006 (onde roda), ADR-005 (protocolo de tools)

---

## Contexto

A Sexta-Feira precisa de uma linguagem para o core: Context Engine, memória, Policy Engine, Planner, Executor e a camada de conversa. A escolha afeta velocidade de desenvolvimento durante 12 meses e o custo de cada fase do roadmap (§15).

Restrições reais do projeto:

- **Carga de trabalho I/O-bound.** A Sexta passa a maior parte do tempo esperando resposta de rede — LLM, GitHub, calendário, agentes. Quase nada é CPU-bound.
- **Concorrência necessária, paralelismo real não.** Precisa rodar agentes e tarefas simultaneamente, mas simultaneidade aqui é esperar várias coisas ao mesmo tempo, não computar várias ao mesmo tempo.
- **Ecossistema de IA é usado pesadamente nos meses 6-10.** Embeddings, avaliação, busca vetorial, reranking, ferramentas de agente.
- **Código que exige disciplina de tipos.** Policy Engine, estado estruturado, log de auditoria e schemas de tool são exatamente onde erro de tipo vira bug de segurança.
- **O aprendizado de baixo nível já está coberto em outro lugar.** M1 usa C (CS50, nand2tetris) e M3 usa C nos labs do xv6. A linguagem do core não precisa carregar valor pedagógico de sistemas.

---

## Opções consideradas

### A. Python 3.12+

**A favor**
- Ecossistema de IA dominante. Todo SDK de LLM, cliente de vector store e ferramenta de avaliação nasce em Python primeiro. A vantagem se concentra exatamente nos meses 6-10, que são a parte difícil do projeto.
- `asyncio` cobre bem o modelo I/O-bound.
- Velocidade de iteração alta, o que importa muito num projeto de 12 meses tocado nas horas livres.
- Ferramentas de tipagem maduras: `mypy --strict`, `pydantic` para validação em runtime nas fronteiras.

**Contra**
- Tipagem estática é opcional e exige esforço deliberado para manter. Sem disciplina, degrada.
- GIL limita paralelismo CPU-bound. Irrelevante aqui, mas é uma porta fechada se o perfil de carga mudar.
- Empacotamento e gestão de ambiente continuam sendo um ponto de atrito.

### B. TypeScript / Node

**A favor**
- Tipagem estática por padrão, não por esforço. Ganho direto no Policy Engine e nos schemas de tool.
- SDK do MCP é de primeira classe.
- Provavelmente mais próximo da experiência atual do Davi — menor energia de ativação nos primeiros meses.
- Modelo assíncrono nativo e maduro.

**Contra**
- Ecossistema de IA claramente atrás. O custo não aparece no começo — aparece no M7 e explode no M9, quando embeddings, avaliação e experimentação de recuperação viram o trabalho principal.
- Resultado provável: acabar escrevendo Python de qualquer jeito para os experimentos, e manter duas linguagens sem ter escolhido isso.

### C. Go

**A favor**
- Excelente para o Executor, concorrência e os temas do M3 e M11.
- Binário único, deploy trivial — casa bem com a migração para VPS do ADR-006.
- Tipagem estática, ferramental simples.

**Contra**
- Ecossistema de IA fraco. Muito trabalho de plumbing manual justamente onde queremos velocidade.
- Curva de aprendizado logo no M1, quando a prioridade é ter algo rodando.
- Risco concreto de matar a velocidade do projeto nos dois primeiros meses, que é quando projetos pessoais morrem.

### D. Rust

Descartado sem análise longa. Melhor valor pedagógico sobre modelo de memória, pior velocidade de entrega. Num projeto de 12 meses tocado em horas livres, é a escolha com maior probabilidade de nunca sair da Fase 0.

---

## Decisão

**Python 3.12 ou superior para o core.**

Com as seguintes condições, que fazem parte da decisão e não são sugestão:

1. **`mypy --strict` desde o primeiro commit.** Tipagem não é opcional neste projeto. Se for adicionada depois, não será adicionada.
2. **`pydantic` em todas as fronteiras** — entrada de tool, saída de tool, estado persistido, política. Validação em runtime onde dado não-confiável entra.
3. **`asyncio` como modelo de concorrência**, decidido agora e não misturado com threads depois.
4. **Escape hatch explícito:** qualquer componente que precise de outra linguagem atravessa uma fronteira de processo (subprocess ou serviço), nunca FFI. Isso mantém o core substituível e casa com a fronteira de rede do ADR-006.

---

## Consequências

**Positivas**
- Meses 6 a 10 ficam significativamente mais baratos.
- Uma linguagem só, do começo ao fim. Sem bifurcação não-planejada.
- Prototipagem rápida de estratégias de memória e recuperação — que é onde vai ter mais tentativa e erro.

**Negativas, aceitas conscientemente**
- Disciplina de tipos passa a ser responsabilidade contínua, não garantia do compilador. `mypy --strict` no CI é a mitigação; se ele for desligado "temporariamente", a decisão foi revogada na prática.
- Empacotamento e ambiente vão dar trabalho na migração para VPS (Fase 5). Mitigação: container desde cedo.
- Se algum dia surgir carga CPU-bound relevante, ela sai do core via fronteira de processo — não vira motivo para reescrever.

**Neutras**
- Não afeta o ADR-009 (substituibilidade de provider de LLM), que é resolvido por abstração, não por linguagem.

---

## Quando revisitar

Esta decisão deve ser reaberta se:

- O perfil de carga virar CPU-bound de forma dominante — o que hoje não há razão para esperar.
- `mypy --strict` estiver desligado por mais de duas semanas. Isso é sinal de que o custo da tipagem opcional superou o benefício do ecossistema.
- No M12, o teste de troca de provider expuser acoplamento causado pela linguagem, e não pela arquitetura.

**Não** deve ser reaberta por preferência estética nem por benchmark isolado.