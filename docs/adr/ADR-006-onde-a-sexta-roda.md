# ADR-006 — Onde a Sexta-Feira roda

**Status:** DECIDIDO
**Data:** 14/08/2026
**Decisor:** Davi
**Relacionado:** ADR-001 (linguagem), ADR-007 (modelo de execução), ADR-011 (isolamento)

---

## Contexto

A Sexta precisa de um lugar para existir. A escolha impacta disponibilidade, custo, privacidade, acesso às ferramentas do Davi e complexidade operacional.

O fator decisivo está no §12 do TS: **proatividade exige estar sempre ligada.** Uma Sexta que só existe quando o PC está aberto não entrega briefing às 8h nem detecta bloqueio durante o dia.

Mas há uma tensão importante: as ferramentas que mais importam — repositório, arquivos, terminal, VS Code — estão na máquina do Davi, não na nuvem. Um core remoto sem braço local é um core sem mãos.

Também vale registrar: as Fases 0 a 3 (fundação, memória, tools, execução de tarefas) **não exigem uptime nenhum.** Construir infraestrutura de disponibilidade antes da Fase 5 seria otimização prematura — e o §17 lista isso explicitamente como algo que o Claude não deve fazer.

---

## Opções consideradas

### A. Local, e só local

**A favor:** custo zero, privacidade máxima, zero atrito de infra, acesso direto a todas as tools.
**Contra:** abre mão da proatividade do §12 por completo. A Sexta vira ferramenta sob demanda, não entidade contínua — o que contradiz a visão do §1.

### B. VPS desde o dia 1

**A favor:** sempre ligada, aprende deploy cedo, força boa higiene de configuração.
**Contra:** adiciona atrito em toda iteração durante quatro fases que não precisam disso. Nas Fases 0-3 você paga o custo e não recebe o benefício. E o acesso às tools locais continua sendo problema não resolvido — só que agora desde o começo.

### C. Cloud gerenciada

**Contra:** custo maior, lock-in, e aprende-se menos. Descartada — a camada gerenciada esconde exatamente o que o M4 e o M11 querem ensinar.

### D. Faseada: local agora, híbrido depois

**A favor:** cada fase paga só o custo que ela precisa. Migração acontece quando há motivo real (Fase 5), não por antecipação.
**Contra:** exige disciplina de projeto agora para que a migração não doa depois.

---

## Decisão

**Abordagem faseada.**

### Fases 0 a 3 — 100% local

Core, memória, tools e executor rodando na máquina do Davi. Sem VPS, sem container em produção, sem deploy.

Justificativa: nenhuma dessas fases tem requisito de disponibilidade. O critério de saída de cada uma (§15) é funcional, não operacional.

### Fase 5 — híbrido

Quando a proatividade entrar:

```
┌─────────────────┐         ┌──────────────────┐
│  CORE (VPS)     │◄───────►│  AGENT (PC)      │
│                 │  rede   │                  │
│  Conversa       │         │  Git / arquivos  │
│  Memória        │         │  Terminal        │
│  Context Engine │         │  Coding agents   │
│  Policy Engine  │         │  Tools locais    │
│  Scheduler      │         │                  │
└─────────────────┘         └──────────────────┘
```

Core na VPS porque precisa de uptime. Executor no PC porque é lá que estão as mãos.

### A condição que faz isso funcionar

**A fronteira entre core e executor é desenhada como se já fosse rede, desde a Fase 2.**

Concretamente, isso significa:

1. Toda tool request atravessa uma interface serializável — não uma chamada de função direta.
2. Nenhum estado compartilhado em memória entre core e executor.
3. Toda operação do executor assume que pode falhar por rede, demorar, ou ser entregue duas vezes.
4. Executor é um serviço local hoje, remoto amanhã — o core não sabe a diferença.

Isso custa quase nada agora. Não fazer isso significa reescrever a camada de execução inteira na Fase 5.

**Importante:** isto não é construir a distribuição agora. É só não assumir in-process. A diferença é grande e o §17 é explícito sobre não otimizar prematuramente.

---

## Consequências

**Positivas**
- Fases 0-3 sem atrito de infra, que é quando velocidade importa mais.
- Custo zero até a Fase 5.
- A migração acontece no M11 (sistemas distribuídos), quando você tem o repertório para fazê-la bem. Antes disso, você faria mal.
- A fronteira serializável melhora o design mesmo se a migração nunca acontecer — testabilidade e isolamento saem de brinde.

**Negativas, aceitas conscientemente**
- Sem proatividade até a Fase 5. A Sexta será útil, mas não contínua no sentido pleno do §12.
- A disciplina da fronteira exige vigilância. Uma chamada direta de conveniência no Executor, aceita "só desta vez", quebra a decisão silenciosamente. Este é o risco real deste ADR.
- Container e empacotamento viram trabalho concentrado na Fase 5 em vez de diluído.

**Mitigação do risco principal**
A fronteira core↔executor deve ter teste que a exercita como se fosse remota — serialização real, latência simulada, falha injetada. Se esse teste não existir, a fronteira vai apodrecer sem ninguém perceber.

---

## Quando revisitar

- **Gatilho de migração:** início da Fase 5. Não antes, mesmo que dê vontade.
- **Reabrir antes** apenas se surgir necessidade real de uptime numa fase anterior — por exemplo, se a Sexta virar dependência de algum fluxo diário do Davi antes da Fase 5.
- **Revisar a decisão de VPS especificamente** no M11, com o repertório de sistemas distribuídos já formado. A escolha de provedor e topologia fica em aberto até lá, de propósito.