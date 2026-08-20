"""O loop.

Este arquivo é o único que sabe que existe um teclado e uma tela. Os outros
três não fazem ideia — e é isso que permite, na Fase 5, trocar o terminal por
Telegram/web/voz mexendo só aqui (ADR-008, ainda em aberto justamente por isso).

Repare no que ele NÃO faz: não sabe que a persistência é JSON, não sabe qual
provider está do outro lado, e não importa SDK nenhum — nem os erros deles.
Conhece dois contratos (`ConversationStore`, `LLMProvider`) e uma exceção do
projeto (`FalhaDoProvider`). As implementações concretas aparecem só dentro do
`construir()`.
"""

import asyncio
import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from friday.llm import (
    AnthropicProvider,
    FalhaDoProvider,
    GeminiProvider,
    LLMProvider,
)
from friday.models import Conversa, Mensagem
from friday.store import (
    ArquivoDeConversaCorrompido,
    ConversationStore,
    JSONConversationStore,
)

# Ancorado na raiz do projeto, e não em `Path("dados/...")` relativo. Um
# caminho relativo é resolvido a partir de ONDE VOCÊ RODOU o comando, não de
# onde o arquivo está: rodar de outra pasta criaria uma segunda conversa vazia
# em silêncio, e a Sexta "esqueceria" tudo sem erro nenhum.
# __file__ = friday/main.py -> .parent = friday/ -> .parent = raiz do projeto
RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_DA_CONVERSA = RAIZ_DO_PROJETO / "dados" / "conversa.json"

COMANDOS_DE_SAIDA = frozenset({"/sair", "/exit", "/quit"})

PROMPT_DO_USUARIO = "\nvocê > "
PREFIXO_DA_SEXTA = "\nsexta > "


# Qual modelo usar não é decisão de código — é de configuração. Fica no .env,
# junto das chaves, e trocar não exige editar nem recompilar nada.
PROVIDERS_CONHECIDOS = ("gemini", "anthropic")
PROVIDER_PADRAO = "gemini"

# Cada provider procura a chave dele numa variável diferente. Só serve para dar
# um erro decente quando ela falta — o SDK acha a chave sozinho, nós não a
# lemos nem a passamos adiante.
CHAVE_ESPERADA = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def construir() -> tuple[ConversationStore, LLMProvider]:
    """Monta as peças concretas — o único lugar do arquivo que as conhece.

    Note as ANOTAÇÕES: o retorno é declarado como as INTERFACES
    (`ConversationStore`, `LLMProvider`), não como as classes concretas. Isso
    não é enfeite: é o que faz o mypy recusar, no resto do arquivo, qualquer
    uso de um método que só exista numa implementação específica. Acoplamento
    indevido vira erro de verificação em vez de descoberta tardia.

    É também aqui que o mypy confere se as classes concretas de fato satisfazem
    os `Protocol`. Como `provider` é declarado UMA vez como `LLMProvider` e os
    dois ramos do `if` atribuem nele, o verificador checa os DOIS providers
    contra a interface nesta função. Se o `GeminiProvider` tivesse a assinatura
    errada, o erro apareceria aqui — antes de rodar, antes de gastar chamada.
    """
    store: ConversationStore = JSONConversationStore(CAMINHO_DA_CONVERSA)

    escolhido = os.getenv("FRIDAY_PROVIDER", PROVIDER_PADRAO).strip().lower()

    if escolhido not in PROVIDERS_CONHECIDOS:
        raise SystemExit(
            f"FRIDAY_PROVIDER='{escolhido}' não existe. "
            f"Use um destes: {', '.join(PROVIDERS_CONHECIDOS)}."
        )

    variavel = CHAVE_ESPERADA[escolhido]
    if not os.getenv(variavel):
        raise SystemExit(
            f"""Falta a variável {variavel} para usar o provider '{escolhido}'.
Ponha ela no arquivo .env — veja o .env.example.
  gemini    -> chave grátis em aistudio.google.com/apikey
  anthropic -> console.anthropic.com (precisa de créditos)"""
        )

    # A única linha do projeto inteiro que sabe quais providers existem.
    provider: LLMProvider
    if escolhido == "gemini":
        provider = GeminiProvider()
    else:
        provider = AnthropicProvider()

    print(f"[provider: {escolhido}]")
    return store, provider


async def ler_entrada(prompt: str) -> str:
    """Lê uma linha do teclado sem travar o event loop.

    `input()` é bloqueante: enquanto ele espera o Enter, NADA mais roda no
    programa. Num programa asyncio isso congela o loop inteiro. `to_thread`
    manda a espera para uma thread e devolve o controle — mesma técnica do
    `store.py`, mesma razão.

    Hoje não há nada concorrente para rodar em paralelo, então isso não muda
    nada de visível. Muda no dia em que houver — e aí a mudança já está feita.
    """
    return await asyncio.to_thread(input, prompt)


async def responder_e_gravar(
    conversa: Conversa,
    store: ConversationStore,
    provider: LLMProvider,
    texto_do_usuario: str,
) -> str | None:
    """Uma volta completa: registra a fala, pergunta ao modelo, registra a resposta.

    A ORDEM aqui é a decisão que importa, e ela é deliberada:

        1. registra a fala do Davi na conversa
        2. SALVA          <-- antes de falar com a API
        3. chama a API
        4. registra a resposta
        5. SALVA

    O passo 2 parece redundante — por que gravar duas vezes? Porque entre ele e
    o passo 5 existe uma chamada de rede, que é a coisa mais provável de falhar
    no programa inteiro: internet cai, chave expira, rate limit, timeout de dez
    minutos. Sem o passo 2, uma falha ali apagaria o que o Davi acabou de
    escrever, e ele reabriria o programa sem sinal nenhum de que a mensagem
    existiu.

    Com o passo 2, o pior caso é uma pergunta registrada sem resposta. Feio,
    mas honesto — e recuperável, porque o histórico dela continua ali.
    """
    conversa.adicionar(Mensagem(role="user", content=texto_do_usuario))
    await store.salvar(conversa)

    try:
        texto_da_resposta = await provider.responder(conversa.mensagens)
    except FalhaDoProvider as erro:
        # UMA classe, do nosso projeto. Não `anthropic.APIError`, não
        # `genai_errors.APIError`. Este arquivo não importa SDK nenhum e não
        # sabe o nome de exceção de fornecedor nenhum — se amanhã entrar um
        # terceiro provider, esta linha continua valendo sem ser tocada.
        #
        # (`RespostaVazia` herda de `FalhaDoProvider`, então continua coberta.)
        #
        # Falha de API NÃO derruba a sessão. Uma internet que oscilou não
        # deveria custar a conversa: avisa, e devolve o controle para o loop.
        print(f"\n[a chamada falhou: {erro}]", file=sys.stderr)
        print("[sua mensagem foi salva; tente de novo]", file=sys.stderr)
        return None

    conversa.adicionar(Mensagem(role="assistant", content=texto_da_resposta))
    await store.salvar(conversa)

    return texto_da_resposta


def _forcar_utf8_na_saida() -> None:
    """Garante que acento não vire lixo ao escrever no terminal.

    Duas coisas diferentes que é fácil confundir:

    - O encoding do ARQUIVO, no `store.py`, nós fixamos à mão
      (`encoding="utf-8"`). O disco está seguro.
    - O encoding da SAÍDA do terminal é outro canal, e o Python o herda do
      sistema. No Windows em português isso costuma ser cp1252 ou cp850 — não
      UTF-8. Um "você" escrito nesse canal vira "voc?" ou explode com
      UnicodeEncodeError.

    Num terminal interativo o Python contorna isso sozinho, então o bug fica
    escondido até o dia em que você redireciona a saída para um arquivo de log
    — e aí aparece de uma vez, num contexto que não sugere encoding nenhum.

    `errors="replace"` é escolha consciente: se ainda assim algum caractere não
    couber, ele vira "?" em vez de derrubar o programa. Uma letra feia é melhor
    que uma sessão perdida.
    """
    for fluxo in (sys.stdout, sys.stderr):
        # `isinstance` e não `try/except`: só `TextIOWrapper` tem
        # `reconfigure`, e checar o tipo deixa o mypy conferir a chamada em vez
        # de engolir um `getattr` que ele não consegue verificar.
        if isinstance(fluxo, io.TextIOWrapper):
            fluxo.reconfigure(encoding="utf-8", errors="replace")


async def main() -> None:
    _forcar_utf8_na_saida()

    # Lê o `.env` e joga as variáveis para dentro do ambiente do processo. Tem
    # que vir ANTES de construir o provider: é assim que `AsyncAnthropic()`
    # encontra a `ANTHROPIC_API_KEY` sem que ela apareça em nenhuma linha de
    # código nossa.
    load_dotenv()

    store, provider = construir()

    try:
        conversa = await store.carregar()
    except ArquivoDeConversaCorrompido as erro:
        # Aqui SIM o programa para. Continuar significaria começar do zero por
        # cima de uma memória que ainda existe no disco — e o primeiro `salvar`
        # a sobrescreveria de vez. Melhor não abrir do que abrir destruindo.
        print(f"\n{erro}", file=sys.stderr)
        raise SystemExit(1) from erro

    if conversa.mensagens:
        quantas = len(conversa.mensagens)
        plural = "mensagem" if quantas == 1 else "mensagens"
        print(f"[continuando — {quantas} {plural} na memória dela]")
    else:
        print("[conversa nova]")
    print("[/sair para encerrar, ou Ctrl+C]")

    while True:
        try:
            entrada = (await ler_entrada(PROMPT_DO_USUARIO)).strip()
        except (EOFError, KeyboardInterrupt):
            # EOFError = Ctrl+D / pipe fechado. Ambos são "acabou", não erro.
            # A saída pode ser tranquila porque nada está pendente: cada troca
            # já foi salva no momento em que aconteceu. Não existe "salvar ao
            # sair" neste programa, e é por isso que arrancar a tomada custa,
            # no máximo, a última resposta.
            break

        if not entrada:
            continue

        if entrada.lower() in COMANDOS_DE_SAIDA:
            break

        resposta = await responder_e_gravar(conversa, store, provider, entrada)

        if resposta is not None:
            print(f"{PREFIXO_DA_SEXTA}{resposta}")

    print("\n[até logo — ela lembra]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Rede de segurança: um Ctrl+C que chegue enquanto o programa está
        # esperando a API (e não o teclado) sobe até aqui. Sem este `except`,
        # o usuário levaria um traceback de vinte linhas na cara ao fazer algo
        # perfeitamente normal.
        print("\n[interrompido]")
