# ESTADO — onde a construção parou

Documento de retomada. Serve para abrir uma sessão nova (outra máquina, outro
dia, outro assistente) e saber em dois minutos o que existe, o que foi decidido
e qual é a próxima linha a escrever.

**Atualize este arquivo ao fim de cada sessão de trabalho.** Se ele mentir, ele
é pior que não existir.

**Última atualização:** 2026-08-18 · Fase 0 — Fundação

---

## 1. O QUE JÁ FUNCIONA

**Ambiente** — pronto e verificado.

- `.venv` com Python 3.14.7
- `anthropic 0.122.0` · `pydantic 2.13.4` · `python-dotenv 1.2.3` · `mypy 2.3.1`
- `.env` com a `ANTHROPIC_API_KEY` preenchida, e coberto pelo `.gitignore`
- `pyproject.toml` com `mypy --strict`, `warn_unreachable` e o plugin do pydantic

**Código** — `friday/models.py` tem a classe `Mensagem`, com quatro campos:
`id`, `role`, `content`, `timestamp`.

Verificado nesta sessão, rodando de verdade:

- `mypy friday/` passa em `--strict`
- `role` inválido, horário sem fuso e tentativa de editar a mensagem depois de
  criada são todos recusados com `ValidationError`
- ida e volta pelo JSON reconstrói a mensagem idêntica

**Vazios ainda:** `friday/llm.py`, `friday/store.py`, `friday/main.py`.

---

## 2. DECISÕES TOMADAS, E POR QUÊ

O porquê é a parte que importa. Se um dia uma delas for revertida, que seja por
um motivo melhor que o registrado aqui — não por esquecimento.

**`timestamp` existe, e é obrigatório.**
É a única dimensão que permite perguntar "o que é recente?", e "recente" é
metade do critério de qualquer recuperação de memória (Fase 1, ADR-004 em
aberto). Campo novo se adiciona depois; passado que não foi gravado não se
reconstrói.

**`timestamp` é *aware*, sempre em UTC — tipado como `AwareDatetime`.**
Um `datetime` sem fuso é um número sem unidade: não dá para saber que instante
representa, e o Python recusa compará-lo com um que tem fuso (`TypeError`). O
tipo `AwareDatetime` do pydantic *rejeita* um horário sem fuso na fronteira,
inclusive vindo de um JSON antigo no disco. UTC no armazenamento; fuso local é
problema de quem exibe.

**Semântica do `timestamp`:** o instante em que o objeto foi construído no
nosso processo. Para uma mensagem do Davi, quando ele apertou Enter; para uma
da Sexta, quando a resposta foi recebida e embrulhada. **Não** é quando o modelo
gerou os tokens, nem o horário do servidor da Anthropic.

**`id` e `timestamp` usam `Field(default_factory=...)`, nunca `= f()`.**
O corpo de uma classe roda **uma vez só**, no import. Com `= _novo_id()` o
Python guardaria aquele único valor como padrão e toda mensagem da execução
nasceria com o mesmo id — bug silencioso, e fatal para deduplicação. O
`default_factory` recebe a *função* e o pydantic a chama a cada objeto novo.
(Mesma armadilha do clássico `def f(lista=[])`.)

**`id` entra já na Fase 0, mesmo sem consumidor.**
O ADR-006 manda desenhar a fronteira assumindo entrega dupla desde a Fase 2, e
deduplicar sem identidade é impossível.

**`id` é `uuid4`, não `uuid7`.**
O `uuid7` ordena cronologicamente sozinho, mas exige Python 3.14+ enquanto o
ADR-001 declara 3.12+ — usá-lo estreitaria o piso do projeto sem emendar o ADR.
E como o `timestamp` já é gravado explicitamente, a ordenação embutida seria
redundante. Se um dia ordenar por id importar de verdade, emenda-se o ADR com
motivo declarado.

**`role` é `Literal["user", "assistant"]`, não `str`.**
Com `str`, um `"usuário"` com acento é aceito ali e só explode três camadas
depois, numa chamada HTTP, com um erro que não menciona typo nenhum. Padrão a
repetir no projeto inteiro: tornar o estado inválido impossível de construir,
em vez de conferir depois se ele é válido.

**`Mensagem` é `frozen=True`.**
Uma mensagem é registro histórico: aconteceu e não muda. Reescrever uma
mensagem antiga não é atualização, é falsificação de histórico.

**`content` é `str` — dívida registrada.**
Quando entrarem tools (Fase 2), conteúdo deixa de ser texto puro e vira lista
de blocos (texto, pedido de tool, resultado de tool). A migração é consciente:
adivinhar esse formato agora, sem nunca ter escrito uma tool, produziria a
abstração errada.

---

## 3. A PERGUNTA ABERTA — retomar exatamente aqui

**A Sexta tem *uma* conversa ou *várias*?** A resposta muda o desenho do
`store.py` inteiro, e por isso o trabalho parou antes de escrever a `Conversa`.

**Opção A — uma conversa só, contínua.** Um arquivo, uma linha do tempo que
nunca termina; abrir o programa é continuar de onde parou.
*A favor:* é o mais fiel ao "entidade contínua, não chatbot com sessões"; o
critério de saída da Fase 0 cai naturalmente; o `store.py` fica trivial.
*Contra:* a lista cresce para sempre e mandar tudo ao modelo fica caro e lento
— mas o CLAUDE.md **já prevê isso** como o que motiva a Fase 1. É o plano, não
uma surpresa.

**Opção B — várias conversas identificadas.** Cada uma com seu `id`, e o
programa escolhe qual carregar.
*A favor:* espelha o que se conhece de ChatGPT/Claude; não fecha a porta de
separar assuntos.
*Contra:* obriga a responder "qual conversa carregar ao abrir?" já no
`main.py`, o que puxa listagem, seleção e talvez título — interface, que está
explicitamente fora do escopo da Fase 0.

**Recomendação registrada:** opção **A**, mas com a `Conversa` carregando um
`id` mesmo assim. Custa um campo, deixa o modelo pronto para o dia em que
existirem várias, e não força nenhuma decisão de interface agora.

---

## 4. PRÓXIMOS PASSOS, NA ORDEM

A ordem segue a dependência: quem define o vocabulário vem antes de quem fala.

1. **Responder a pergunta da seção 3.**
2. **`models.py` — classe `Conversa`.** Lista de `Mensagem` e o que mais a
   resposta acima exigir. Nota: `Conversa` **não** pode ser `frozen`, porque
   mensagens são acrescentadas a ela — decidir se o acréscimo muda o objeto no
   lugar ou devolve uma cópia nova.
3. **`store.py`** — interface `ConversationStore` + implementação em JSON.
   Persistência em arquivo, não banco: o ADR-002 está em aberto e será decidido
   no mês 5, com repertório. A interface existe para que trocar depois saia
   barato.
4. **`llm.py`** — interface `LLMProvider` + implementação Anthropic. **Nenhum
   arquivo fora daqui importa o SDK da Anthropic** (P1).
5. **`main.py`** — o loop que amarra os três.

**Critério de saída da Fase 0:** conversar → `Ctrl+C` → rodar de novo → ela
lembra do que foi dito.

**Fora do escopo, e resistir a adicionar:** memória de verdade, tools,
permissões, interface bonita.

---

## 5. COMO RETOMAR NA MÁQUINA

```bash
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
mypy friday/
```

Se o `.venv` não existir na máquina nova, ele **não** vem pelo git (está no
`.gitignore`, e é assim que deve ser): crie com `python -m venv .venv` e rode o
`pip install`. O `.env` também não vem pelo git — copie de `.env.example` e
preencha a `ANTHROPIC_API_KEY` de novo, pegando em console.anthropic.com.

---

## 6. NOTA SOBRE UM DIRETÓRIO SOLTO

Existe um `F.R.I.D.A.Y Brain/` na raiz — um vault do Obsidian recém-criado, só
com o arquivo de boas-vindas padrão. Não é código e não está versionado.
Decidir de propósito se ele entra no git ou vai para o `.gitignore`, em vez de
deixá-lo aparecendo como não rastreado para sempre.
