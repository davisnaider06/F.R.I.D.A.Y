# ESTADO — onde a construção parou

Documento de retomada. Serve para abrir uma sessão nova (outra máquina, outro
dia, outro assistente) e saber em dois minutos o que existe, o que foi decidido
e qual é a próxima linha a escrever.

**Atualize este arquivo ao fim de cada sessão de trabalho.** Se ele mentir, ele
é pior que não existir. *(Aconteceu: a versão anterior dizia que só existia a
classe `Mensagem` quando a `Conversa` já estava escrita, e dizia que o vault do
Obsidian não estava versionado quando ele já estava. A sessão começou com
arqueologia em vez de código.)*

**Última atualização:** 2026-08-20 · **Fase 0 — CONCLUÍDA**

---

## 1. O QUE JÁ FUNCIONA

**A Fase 0 fechou.** O critério de saída foi verificado rodando de verdade:
processo novo, RAM zerada, abre lendo o disco e enxerga o que foi dito antes.

**Ambiente**

- `.venv` com Python 3.14.7
- `anthropic 0.122.0` · `pydantic 2.13.4` · `python-dotenv 1.2.3` · `mypy 2.3.1`
- `.env` com a `ANTHROPIC_API_KEY`, coberto pelo `.gitignore` (linha 151)
- `pyproject.toml` com `mypy --strict`, `warn_unreachable` e o plugin do pydantic

**Código — `mypy --strict` passa nos seis arquivos.**

| arquivo | o que faz |
|---|---|
| `models.py` | `Mensagem` (frozen) e `Conversa` (mutável, id frozen no campo) |
| `store.py` | `ConversationStore` (Protocol) + `JSONConversationStore` com escrita atômica |
| `llm.py` | `LLMProvider` (Protocol) + `AnthropicProvider` **e** `GeminiProvider`. **Único arquivo que importa SDK de LLM** |
| `main.py` | o loop: lê teclado, grava, chama, grava. Escolhe o provider pelo `.env` |
| `modelos.py` | `python -m friday.modelos` lista os modelos da sua chave |
| `__init__.py` | vazio |

**Verificado nesta sessão, rodando de verdade:**

- `mypy friday/` passa em `--strict` nos 6 arquivos
- dois processos separados: o segundo abriu com o histórico do primeiro
- o `id` da conversa sobrevive à ida e volta pelo JSON
- escrita atômica não deixa `.tmp` órfão no diretório
- falha de API **não** derruba a sessão, e a mensagem do usuário fica salva
  (testado sem querer, e de graça — ver seção 3)
- acento sai correto mesmo com a saída redirecionada para arquivo
- um `ProviderFalso` que **não herda** de `LLMProvider` encaixa sem o `main.py`
  perceber — o desacoplamento via `Protocol` é real, não só intenção
- **dois providers reais** (Anthropic e Gemini) atrás da mesma interface, com
  a tradução `assistant` → `model` verificada com cliente dublê
- **conversa real ponta a ponta com o Gemini**, em dois processos separados: o
  segundo respondeu "Seu nome é Davi e você me disse que está me construindo"
  lendo só o disco. **O critério de saída da Fase 0 está cumprido de verdade.**
- erro de provider (404 e 503 reais) é capturado, avisado e a sessão continua

**Onde a memória mora:** `dados/conversa.json`, na raiz do projeto. Fora do git
(ver seção 6).

---

## 2. DECISÕES TOMADAS, E POR QUÊ

O porquê é a parte que importa. Se um dia uma delas for revertida, que seja por
um motivo melhor que o registrado aqui — não por esquecimento.

### Sobre os modelos de dados (sessões anteriores)

**`timestamp` existe, é obrigatório, e é *aware* em UTC (`AwareDatetime`).**
É a única dimensão que permite perguntar "o que é recente?", metade do critério
de qualquer recuperação de memória (Fase 1, ADR-004 em aberto). Um `datetime`
sem fuso é um número sem unidade; `AwareDatetime` *rejeita* isso na fronteira,
inclusive vindo de JSON antigo no disco. Campo novo se adiciona depois; passado
que não foi gravado não se reconstrói.

**Semântica do `timestamp`:** o instante em que o objeto foi construído no nosso
processo — não quando o modelo gerou os tokens, nem o horário do servidor da
Anthropic.

**`id` e `timestamp` usam `Field(default_factory=...)`, nunca `= f()`.**
O corpo de uma classe roda uma vez só, no import. Com `= _novo_id()` toda
mensagem da execução nasceria com o mesmo id — fatal para deduplicação.

**`id` é `uuid4`, não `uuid7`.** `uuid7` ordena por tempo sozinho mas exige
3.14+, e o ADR-001 declara 3.12+. Como o `timestamp` já é explícito, a ordenação
embutida seria redundante.

**`role` é `Literal["user", "assistant"]`, não `str`.** Tornar o estado inválido
impossível de construir, em vez de conferir depois se ele é válido.

**`Mensagem` é `frozen`; `Conversa` não é.** Mensagem é registro histórico:
aconteceu e não muda. Conversa é entidade viva que cresce. O `id` da `Conversa`
é frozen **no campo** — ela muda, a identidade dela não.

**`Conversa.adicionar()` muda no lugar e não devolve nada.** A alternativa
(devolver cópia nova) é mais segura sob concorrência, mas o modo de falha hoje é
pior: esquecer o `conversa = ` faria a mensagem sumir sem erro nenhum. Barato de
reverter porque **ninguém fora de `models.py` toca em `mensagens` direto**.

**`content` é `str` — dívida registrada.** Na Fase 2, com tools, vira lista de
blocos. Adivinhar esse formato sem nunca ter escrito uma tool produziria a
abstração errada.

**Uma conversa contínua, não várias.** *(Decidido 2026-08-20.)* Um arquivo, uma
linha do tempo que nunca termina. É o mais fiel a "entidade contínua, não
chatbot com sessões", e não força responder "qual conversa abrir?" no `main.py`
— o que puxaria listagem e seleção, ou seja, interface, explicitamente fora do
escopo da Fase 0. A `Conversa` carrega `id` mesmo assim: custa um campo e deixa
a porta aberta.

### Sobre as três peças novas (2026-08-20)

**`ConversationStore` e `LLMProvider` são `Protocol`, não classes-base.**
Com herança, a implementação precisa importar a interface. Com `Protocol`, ela
só precisa ter os métodos certos e o mypy confere o encaixe sozinho. É o "se
anda como pato" do Python, verificado antes de rodar. Provado na prática: um
dublê de teste encaixou sem herdar nada.

**As interfaces são `async`, mesmo sem nada concorrente na Fase 0.**
O ADR-001 declara asyncio como modelo de concorrência. Em Python `async` é
contagioso (*function coloring*): uma função async só pode ser esperada por
outra async, então converter depois obriga a reescrever a cadeia inteira acima.
Pagar agora custa três `await`; pagar depois custa três arquivos. Somado ao
ADR-006 ("desenhe a fronteira como se já fosse rede"), a assinatura já está
certa para o dia em que o store estiver do outro lado de um socket.

**I/O de disco roda em `asyncio.to_thread`.** `open`/`write` bloqueiam, e uma
chamada bloqueante dentro de um programa asyncio trava o event loop inteiro.
Irrelevante hoje com arquivo pequeno e local; está lá porque o sintoma desse
erro é "o programa congela de vez em quando", que é quase impossível de achar
depois. Mesma técnica no `input()` do `main.py`.

**A escrita do JSON é atômica: temporário + `os.replace`.**
Abrir o arquivo final para escrita o ZERA antes de escrever o conteúdo novo. Se
o processo morrer nesse intervalo, sobra um arquivo pela metade — e o critério
de saída da Fase 0 é *literalmente apertar Ctrl+C*, então a janela de risco é o
fluxo de uso normal, não um caso raro. `os.replace` é atômico: o caminho final
sempre aponta para o conteúdo velho inteiro ou o novo inteiro. O temporário
nasce no **mesmo diretório** porque renomear só é atômico dentro do mesmo
volume. `flush()` + `fsync()` antes, para não publicar conteúdo que ainda está
em cache do sistema operacional.

**JSON corrompido levanta exceção; NÃO recomeça do zero.**
`ArquivoDeConversaCorrompido` é exceção própria para separar "nunca houve
conversa" (arquivo ausente — normal) de "havia e está ilegível" (grave). Um
`return Conversa()` silencioso apagaria a memória dela sem avisar, que é o pior
modo de falha possível num projeto cujo ponto inteiro é lembrar. O `main.py`
para com `SystemExit(1)`: melhor não abrir do que abrir destruindo.

**A ordem de gravação é: salva a fala do usuário ANTES de chamar a API.**
Entre a fala e a resposta existe uma chamada de rede — a coisa mais provável de
falhar no programa inteiro. Sem o salvamento antecipado, uma falha ali apagaria
o que o Davi acabou de escrever, sem sinal nenhum. Com ele, o pior caso é uma
pergunta registrada sem resposta: feio, mas honesto e recuperável.

**Falha de API não derruba a sessão.** `anthropic.APIError` e `RespostaVazia`
são capturados no loop: avisa no stderr e devolve o controle. Internet que
oscilou não deveria custar a conversa.

**Não existe "salvar ao sair".** Cada troca é gravada no momento em que
acontece. É por isso que arrancar a tomada custa, no máximo, a última resposta —
e por isso `Ctrl+C` e `Ctrl+D` podem sair sem cerimônia.

**Modelo: `claude-opus-5`.** Parametrizável no construtor do `AnthropicProvider`
(`modelo=`), não fixo no código.

**A resposta é lida filtrando blocos por tipo, nunca `content[0].text`.**
`resposta.content` é uma **lista de blocos**, não uma string. No Opus 5 o
raciocínio vem ligado por padrão e blocos de *thinking* entram nessa lista — o
bloco `[0]` pode perfeitamente não ser texto. O jeito que quase todo tutorial
ensina quebraria aqui.

**`stop_reason` é checado ANTES do conteúdo.** Uma recusa por política volta com
HTTP 200 e cara de sucesso; só o `stop_reason` denuncia.

**`max_tokens = 16_000`.** É teto, não meta — o modelo não tenta preencher. Um
valor baixo trunca a resposta no meio de uma frase sem aviso nenhum.

**A saída do terminal é forçada para UTF-8 no `main.py`.**
Duas coisas diferentes: o encoding do **arquivo** já era fixado à mão no
`store.py`; o encoding da **saída do terminal** é outro canal, herdado do
sistema. Nesta máquina o console é codepage 850 e o Python escreve em cp1252 —
"você" vira "voc?" no instante em que a saída é redirecionada para um log.
`errors="replace"` para que um caractere impossível vire "?" em vez de derrubar
o programa.

### Sobre o segundo provider (2026-08-20)

**Existem dois providers: `AnthropicProvider` e `GeminiProvider`.** O motivo
imediato foi custo (a camada gratuita do Gemini destrava a Fase 0 sem gastar),
mas o ganho real foi outro: **o P1 deixou de ser afirmação e virou fato
verificado.** Enquanto havia um provider só, "o LLM é componente substituível"
era uma intenção não testada. Com dois, `models.py`, `store.py` e `main.py`
continuam sem saber que o Gemini existe.

**A tradução de `role` mora dentro do provider, e só lá.**
A Anthropic diz `"user"`/`"assistant"`; o Google diz `"user"`/`"model"`.
Mesma ideia, nome diferente — e é esse tipo de divergência boba que destrói um
projeto sem fronteira, porque a string se espalha e trocar de provider vira
caça ao literal em vinte arquivos, com erro só em tempo de execução. Aqui é uma
linha, num lugar. *(Confirmado lendo o código do próprio SDK — `chats.py:161`,
`Content(role="model")` — e não a documentação, que estava confusa.)*

**A escolha do provider é configuração, não código.** `FRIDAY_PROVIDER` no
`.env`, lido no `construir()`. Trocar de modelo não edita nenhum `.py`.

**O `construir()` declara `provider: LLMProvider` UMA vez e atribui nos dois
ramos.** Isso não é estilo: é o que faz o mypy conferir os **dois** providers
contra o `Protocol` naquela função. Assinatura errada em qualquer um dos dois
falha ali, antes de rodar.

**`listar_modelos_gemini()` vive no `llm.py`, não num utilitário à parte.**
Porque o P1 proíbe importar SDK fora dele. O `modelos.py` só chama a função —
não conhece o Google. Foi o P1 moldando o desenho na prática, e não no papel.

**Nome de modelo envelhece.** `MODELO_GEMINI_PADRAO = "gemini-3.7-flash"` é
chute informado, tirado da documentação em 2026-08-20, **não verificado contra
a API** (faltava chave). Confirmar com `python -m friday.modelos` e corrigir se
preciso. Descobrir isso por um 404 no meio de uma conversa é a pior hora.

### O bug do vazamento de exceção — e a regra que ele criou (2026-08-20)

**Vale mais que qualquer outra decisão desta sessão, porque foi erro cometido,
não previsto.**

O `main.py` capturava `anthropic.APIError` direto. Passou no mypy, passou no
teste com dublê, funcionou com um provider só. **Quebrou na primeira chamada
real do Gemini**, que levanta `google.genai.errors.ServerError` — classe sem
parentesco nenhum com a da Anthropic. O programa morreu com traceback
exatamente onde o comentário prometia que ele não morreria.

A causa não foi o `except` mal escrito. Foi o `main.py` **precisar conhecer o
nome de uma exceção de um SDK específico**. A abstração vazava — só que pelos
erros, não pelos dados. Ponto cego clássico: todo mundo traduz os dados na
fronteira e esquece que **erro também é dado**.

**Regra que passa a valer:** existe `FalhaDoProvider` (em `llm.py`). Cada
provider embrulha os erros do SDK dele nessa classe. `RespostaVazia` herda dela
— o que de quebra resolveu a inconsistência de hierarquia anotada antes.
**Fora do `llm.py`, nenhum arquivo captura exceção de SDK.** Verificado: um
`grep` por `anthropic|genai|google` no `main.py` só acha strings de
configuração e o comentário que explica a regra.

Isso também mostra o limite do `mypy --strict`: ele prova que os tipos batem,
não que o programa está certo. Só rodar contra a coisa real encontrou isto.

**Automatic function calling do Gemini: DESLIGADO, e não é pelo aviso no log.**
AFC é o SDK executar sozinho as funções que o modelo pedir, devolvendo o
resultado sem passar por nós. Hoje é inofensivo — não há função registrada. Na
Fase 2, com tools, seria um caminho `LLM -> execução` **pulando o Policy
Engine**, que é literalmente o que o P3 proíbe. Desligado agora, com o motivo
escrito, em vez de descoberto depois como porta dos fundos aberta desde agosto.

**Modelo padrão do Gemini: `gemini-3.6-flash`, e não o mais novo.**
Medido em 2026-08-20, quatro chamadas seguidas na camada gratuita:
`3.7-flash` 2/4 · `3.6-flash` 4/4 · `3.5-flash` 3/4 · `3.5-flash-lite` 4/4.
O modelo mais novo é o mais disputado, e o 503 "high demand" é do lado do
Google. A saída correta seria a camada de resiliência (retry/backoff) — que o
ADR-013 lista como **construir, no M4**. Escrevê-la agora queimaria um
entregável da trilha por pressa. Registrada, não feita.

*Aprendido de raspão:* `gemini-2.5-flash` aparece na listagem mas dá 404 em
`generateContent`. Estar na lista não garante que serve para o que você quer.

---

## 3. NÃO HÁ BLOQUEIO

A Fase 0 roda ponta a ponta com o Gemini na camada gratuita, custo zero.

**Sobre a conta da Anthropic:** continua sem créditos (`400 invalid_request_error
— credit balance is too low`). Isso NÃO trava nada: `FRIDAY_PROVIDER=gemini` no
`.env` é o padrão. Para usar o Claude um dia, compre créditos em
console.anthropic.com e troque a variável — nenhuma linha de código muda.

**Vale gravar, porque é fonte comum de confusão:** a assinatura do Claude
(claude.ai / Claude Code, mensal) e a **API** (console.anthropic.com, pré-paga)
são **produtos separados com faturamentos separados**. A assinatura não dá
acesso à API. Isso vale inclusive para o **Claude Agent SDK**, que a própria
documentação manda autenticar com chave de API.

**Sobre o Claude Agent SDK como base da Sexta: descartado, pelo ADR-013.**
Ele entrega agent loop, context management, permissions, sessions e memory —
que é, quase item por item, a lista de CONSTRUIR do ADR-013 (M8, M9, M10, Fase
2, Fase 4). O desempate mecânico ("é entregável de algum mês?") dá sim para
todos. Some-se a regra 2 do mesmo ADR ("nunca dois sistemas de permissão
concorrentes"): ele traz o dele pronto. Fica como **objeto de estudo no M10**,
no mesmo papel dado ao OpenClaw. Não precisou de ADR novo — a categoria já
estava decidida, que era exatamente o propósito do ADR-013.

## 4. PRÓXIMOS PASSOS, NA ORDEM

1. **Resolver os créditos** e rodar `python -m friday.main` de verdade. Falar
   duas coisas, sair, reabrir, perguntar se ela lembra.
2. **Sentir a armadilha da Fase 0 acontecendo.** O `main.py` manda a conversa
   INTEIRA ao modelo a cada mensagem. Isso funciona por alguns dias e depois
   fica caro, lento, e ela se perde. **Isto é esperado e é o ponto** — é o que
   motiva a Fase 1. Não conserte agora. Observe: veja o custo por mensagem
   subir e a latência crescer. A Fase 1 fica muito mais fácil de projetar para
   quem sentiu o problema do que para quem só leu sobre ele.
3. **Fase 1 — memória de verdade.** Depende de ADR-003 (vetorial) e ADR-004
   (recuperação), ambos **em aberto**. Não começar sem decidi-los.

### Dívidas pequenas, conscientes, não urgentes

- **Nenhum teste automatizado.** A validação desta sessão foi manual e por
  script descartável. Vale um `pytest` antes da Fase 1 — o `Protocol` já deixa
  os dublês triviais de escrever, que era a parte cara.
- **Sem streaming.** A resposta aparece de uma vez, depois da espera inteira.
  Melhoraria muito a sensação de uso, mas "interface bonita" está fora do
  escopo da Fase 0. Candidata a primeira melhoria depois que a Fase 1 fechar.
- **Sem retentativa própria.** O SDK já retenta 429 e 5xx duas vezes sozinho.
  Só vale escrever a nossa se isso provar ser insuficiente.
- **`RespostaVazia` herda de `RuntimeError`;** `ArquivoDeConversaCorrompido` de
  `Exception`. Inconsistente. Sem consequência hoje.

---

## 5. COMO RETOMAR NA MÁQUINA

```bash
# Ativar o venv — a forma MUDA conforme o terminal:
.\.venv\Scripts\Activate.ps1   # PowerShell (o `.\` na frente é obrigatório)
.venv\Scripts\activate.bat     # cmd.exe
source .venv/bin/activate      # Mac/Linux

pip install -r requirements.txt
mypy friday/
python -m friday.modelos       # confere os modelos que a sua chave enxerga
python -m friday.main
```

**Armadilha já vivida (2026-08-20):** sem ativar o venv, `python` resolve para
o Python do sistema (`WindowsApps\python.exe`), que não tem as dependências. O
erro é `ModuleNotFoundError: No module named 'dotenv'` — parece falta de
instalação, e não é: é o interpretador errado. A versão anterior deste arquivo
mandava `.venv\Scripts\activate`, que é a forma do **cmd.exe** e falha no
PowerShell, porque lá caminho relativo exige o `.\` na frente.

Alternativa que dispensa ativar, e funciona em qualquer terminal:
`.\.venv\Scripts\python.exe -m friday.main`

Se o `.venv` não existir na máquina nova, ele **não** vem pelo git (está no
`.gitignore`, e é assim que deve ser): crie com `python -m venv .venv` e rode o
`pip install`. O `.env` também não vem — copie de `.env.example` e preencha a
`ANTHROPIC_API_KEY` de novo, pegando em console.anthropic.com.

`dados/conversa.json` também não vem pelo git: numa máquina nova ela começa sem
memória. É intencional (seção 6).

---

## 6. O VAULT DO OBSIDIAN — decidido

*(A versão anterior deste documento dizia que o `F.R.I.D.A.Y Brain/` não estava
versionado. Estava — entrou no commit `63df0c0`.)*

**Decisão:** as **notas** entram no git; a **configuração de janela** do
Obsidian, não.

O porquê: neste projeto o raciocínio é o produto e o código é subproduto —
perder as notas custaria mais que perder qualquer arquivo de `friday/`. Já o
`workspace.json` guarda que painel estava aberto e onde, muda sozinho toda vez
que o app abre, e encheria o histórico de commits sem conteúdo.

Feito: `git rm --cached` no `workspace.json` (**o arquivo continua no disco** —
`--cached` mexe só no índice do git) e as regras no `.gitignore`. Isso foi
necessário porque **`.gitignore` não tem efeito sobre arquivo já rastreado**:
sem tirar do índice antes, a regra seria letra morta.

Estado atual do vault: **zero notas**, só a pasta `.obsidian/`.

**`dados/` fica fora do git**, e isso é decisão separada: é conteúdo privado de
conversa, muda a cada mensagem, e é estado da *máquina*, não do projeto. Duas
máquinas com a memória dela versionada dariam conflito de merge em cima da
própria memória — exatamente o tipo de coisa que não se resolve escolhendo um
lado. Sincronizar entre máquinas é problema da Fase 5 (ADR-006), com solução
de verdade.
