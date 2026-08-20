"""A única porta de saída para um modelo de linguagem.

**Este é o único arquivo do projeto autorizado a importar o SDK da Anthropic**
(P1: "o sistema importa mais que o modelo; o LLM é componente substituível").

A regra parece burocracia até você tentar quebrá-la. Se `main.py` importasse
`anthropic` direto, o formato da API viraria o formato interno da Sexta por
osmose — os `{"role": ..., "content": ...}` da Anthropic iam vazando para
todo lado, e trocar de provider deixaria de ser "escrever uma classe nova"
para virar "reescrever o programa". A tradução entre o vocabulário dela
(`Mensagem`, de `models.py`) e o vocabulário da API acontece aqui dentro, e
em nenhum outro lugar.
"""

from collections.abc import Sequence
from typing import Final, Protocol

from anthropic import APIError as ErroDaAnthropic
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from friday.models import Mensagem

# `Final` diz ao mypy: isto não é reatribuído em lugar nenhum. Não é constante
# de verdade (Python não tem), mas o verificador passa a acusar quem tentar.

MODELO_PADRAO: Final = "claude-opus-5"

# Confira os modelos disponíveis com `python -m friday.modelos` — a lista muda
# com o tempo e não vale confiar em constante velha.
#
# NÃO é o modelo mais novo, e isso é escolha. Medido em 2026-08-20, quatro
# chamadas seguidas na camada gratuita:
#     gemini-3.7-flash       2/4   (o mais novo é o mais disputado)
#     gemini-3.6-flash       4/4
#     gemini-3.5-flash       3/4
#     gemini-3.5-flash-lite  4/4
# O 503 "high demand" é do lado do Google, não nosso, e nenhuma retentativa
# nossa o resolveria de forma barata. Trocar de modelo custa uma linha.
#
# A saída certa para isso é a camada de resiliência de rede — que o ADR-013
# lista como CONSTRUIR, no M4. Escrever retry/backfoff agora seria queimar um
# entregável da trilha por pressa. Fica registrado, não feito.
MODELO_GEMINI_PADRAO: Final = "gemini-3.6-flash"

# Teto, não meta. É onde a resposta é CORTADA no meio se ela crescer demais —
# o modelo não tenta preencher o valor. Deixar baixo demais é o erro comum:
# a resposta chega truncada na metade de uma frase e não há aviso nenhum além
# de `stop_reason == "max_tokens"`.
MAX_TOKENS_PADRAO: Final = 16_000

PROMPT_DE_SISTEMA: Final = """Você é a Sexta-Feira, a IA pessoal do Davi.

Você não é um assistente genérico começando do zero a cada conversa: você é
uma entidade contínua. A conversa que você está vendo pode ter começado dias
atrás, e continua sendo a mesma.

O Davi está aprendendo a programar de verdade, vindo de vibe coding. Explique
o porquê das coisas, não só o como. Discorde quando tiver motivo.

Seja direta. Sem preâmbulo, sem elogiar a pergunta, sem resumir no fim o que
você acabou de dizer."""


class FalhaDoProvider(RuntimeError):
    """Não foi possível obter uma resposta do modelo. Qualquer que seja o motivo.

    Esta classe existe por causa de um bug real, cometido nesta mesma sessão.

    O `main.py` capturava `anthropic.APIError` diretamente. Funcionou enquanto
    havia um provider só — e quebrou no primeiro erro do Gemini, que levanta
    `google.genai.errors.ServerError`, uma classe sem parentesco nenhum com a
    da Anthropic. O programa morreu com traceback exatamente onde estava
    escrito que ele não morreria.

    A causa não foi o `except` mal escrito. Foi o `main.py` PRECISAR conhecer
    o nome de um erro de um SDK específico — ou seja, a abstração vazava, só
    que pelas exceções em vez de pelos dados. É um ponto cego comum: todo mundo
    lembra de traduzir os dados na fronteira e esquece que erro também é dado.

    A regra que passa a valer: **provider traduz o erro do SDK dele para esta
    classe.** Fora do `llm.py`, ninguém captura exceção de SDK nenhum.
    """


class RespostaVazia(FalhaDoProvider):
    """O modelo respondeu, mas sem nenhum bloco de texto.

    Acontece de verdade — por exemplo, quando o modelo recusa a requisição por
    política (`stop_reason == "refusal"`). Vira exceção própria para que quem
    chama possa tratar sem inspecionar string de mensagem de erro.
    """


class LLMProvider(Protocol):
    """O contrato de "algo capaz de continuar uma conversa".

    Repare no que a assinatura NÃO tem: nada de `model`, `max_tokens`,
    `system`, `temperature`. Esses são detalhes de como a Anthropic expõe a
    coisa hoje — se vazassem para cá, a interface estaria acorrentada a um
    provider específico e não valeria nada. Eles moram no construtor da
    implementação concreta, embaixo.

    Entra: a conversa até agora. Sai: o que ela responde. É o contrato mínimo.
    """

    async def responder(self, mensagens: Sequence[Mensagem]) -> str:
        """Recebe a conversa até aqui e devolve o texto da próxima fala dela."""
        ...


class AnthropicProvider:
    """Implementação do contrato acima usando a API da Anthropic."""

    def __init__(
        self,
        cliente: AsyncAnthropic | None = None,
        modelo: str = MODELO_PADRAO,
        max_tokens: int = MAX_TOKENS_PADRAO,
    ) -> None:
        """
        `cliente` é injetável (e por isso opcional) para que um teste possa
        passar um dublê no lugar do cliente real. Se ele fosse construído aqui
        dentro sem alternativa, testar esta classe exigiria bater na API de
        verdade — lento, caro, e falhando quando a internet cai.

        `AsyncAnthropic()` sem argumentos lê a `ANTHROPIC_API_KEY` do ambiente
        sozinho. É por isso que a chave nunca aparece escrita no código: quem
        põe ela no ambiente é o `load_dotenv()` lá no `main.py`, lendo o `.env`
        — que está no `.gitignore` e nunca vai para o git.
        """
        self._cliente = cliente if cliente is not None else AsyncAnthropic()
        self._modelo = modelo
        self._max_tokens = max_tokens

    async def responder(self, mensagens: Sequence[Mensagem]) -> str:
        # --- Tradução: vocabulário da Sexta -> vocabulário da API ------------
        #
        # Aqui a `Mensagem` perde o `id` e o `timestamp`. É de propósito: a API
        # não tem onde colocá-los e não os quer. Eles existem para NÓS — o `id`
        # para deduplicar (ADR-006) e o `timestamp` para um dia responder "o
        # que é recente?" na recuperação de memória (Fase 1).
        #
        # `MessageParam` é o tipo que o próprio SDK exporta. Usar o dele em vez
        # de inventar um `dict[str, str]` faz o mypy conferir o formato: se um
        # dia a API mudar de campo, o erro aparece aqui, na linha certa, ao
        # rodar `mypy` — e não em produção, num 400 sem explicação.
        historico: list[MessageParam] = [
            {"role": m.role, "content": m.content} for m in mensagens
        ]

        try:
            resposta = await self._cliente.messages.create(
                model=self._modelo,
                max_tokens=self._max_tokens,
                # O prompt de sistema vai num parâmetro PRÓPRIO, e não como uma
            # primeira mensagem de `user`. São coisas diferentes: o `system`
                # tem autoridade sobre o resto da conversa, e — detalhe que vale
                # ouro depois — fica no início do prefixo, que é o que permite
                # cachear ele mais adiante.
                system=PROMPT_DE_SISTEMA,
                messages=historico,
            )
        except ErroDaAnthropic as erro:
            # A tradução: erro do SDK entra, erro do projeto sai. Quem chamou
            # não precisa (nem deve) saber que existe um SDK da Anthropic.
            raise FalhaDoProvider(f"Anthropic: {erro}") from erro

        # --- Leitura da resposta --------------------------------------------
        #
        # `stop_reason` primeiro, SEMPRE, antes de olhar o conteúdo. Uma recusa
        # por política volta com HTTP 200 e cara de sucesso — só o `stop_reason`
        # denuncia. Ler o conteúdo antes de checar isso é como ler o resultado
        # de uma função sem olhar se ela deu erro.
        if resposta.stop_reason == "refusal":
            detalhe = getattr(resposta.stop_details, "explanation", None)
            raise RespostaVazia(f"O modelo recusou a requisição. {detalhe or ''}".strip())

        # `resposta.content` é uma LISTA DE BLOCOS, não uma string. Isto é o que
        # quase todo tutorial ensina errado, com `resposta.content[0].text`.
        #
        # No Claude Opus 5 o raciocínio ("thinking") vem ligado por padrão, e
        # blocos de raciocínio entram nessa lista. O bloco [0] pode
        # perfeitamente não ser texto — e aí `.text` explode com AttributeError,
        # ou vem vazio. Por isso filtramos por tipo em vez de indexar por
        # posição.
        partes = [bloco.text for bloco in resposta.content if bloco.type == "text"]

        if not partes:
            raise RespostaVazia(
                f"Resposta sem nenhum bloco de texto (stop_reason={resposta.stop_reason})."
            )

        return "\n\n".join(partes)


# ===========================================================================
# SEGUNDO PROVIDER — e é aqui que o P1 deixa de ser frase e vira fato.
#
# Repare no que esta classe NÃO precisou mudar em nenhum outro arquivo:
# `models.py`, `store.py` e `main.py` não sabem que o Gemini existe. Eles
# conhecem o `LLMProvider`, e qualquer coisa com o método `responder` na
# assinatura certa entra no lugar. Foi para isto que a interface existiu desde
# o começo, sem consumidor nenhum — o consumidor é este arquivo aqui, agora.
# ===========================================================================


class GeminiProvider:
    """O mesmo contrato `LLMProvider`, atendido pelo Gemini do Google.

    Note que ela também NÃO herda de `LLMProvider`. Nada aqui menciona a
    interface. O encaixe é estrutural — o mypy confere lá no `construir()` do
    `main.py`, onde a anotação declara o tipo como a interface.
    """

    def __init__(
        self,
        cliente: genai.Client | None = None,
        modelo: str = MODELO_GEMINI_PADRAO,
        max_tokens: int = MAX_TOKENS_PADRAO,
    ) -> None:
        """
        Mesma estrutura do `AnthropicProvider`, de propósito: cliente
        injetável para teste, modelo e teto parametrizáveis.

        `genai.Client()` sem argumentos procura a chave no ambiente, em
        `GEMINI_API_KEY` (ou `GOOGLE_API_KEY`). Mesmo padrão do outro provider,
        e pela mesma razão: chave nenhuma aparece escrita no código.
        """
        self._cliente = cliente if cliente is not None else genai.Client()
        self._modelo = modelo
        self._max_tokens = max_tokens

    async def responder(self, mensagens: Sequence[Mensagem]) -> str:
        # --- A TRADUÇÃO, e o motivo de toda essa arquitetura existir ---------
        #
        # A Anthropic chama os dois lados de "user" e "assistant".
        # O Google chama de "user" e "model".
        #
        # Mesma ideia, nome diferente. E é EXATAMENTE esse tipo de divergência
        # boba que arruína um projeto quando não há fronteira: sem esta camada,
        # a string "assistant" estaria espalhada pelo código inteiro, e trocar
        # de provider viraria caça ao literal em vinte arquivos — com o bônus
        # de que o erro só apareceria em tempo de execução, num 400 sem
        # explicação.
        #
        # Aqui, a tradução mora em uma linha, num lugar só. O resto do projeto
        # continua falando o vocabulário da Sexta (`models.py`) e nunca precisa
        # saber que existe essa diferença.
        historico = [
            genai_types.Content(
                role="model" if mensagem.role == "assistant" else "user",
                parts=[genai_types.Part(text=mensagem.content)],
            )
            for mensagem in mensagens
        ]

        try:
            resposta = await self._cliente.aio.models.generate_content(
                model=self._modelo,
                contents=historico,
                # Outra diferença de forma: na Anthropic o prompt de sistema é um
                # parâmetro de primeiro nível (`system=`); aqui ele vai dentro de um
                # objeto de configuração, com outro nome (`system_instruction`).
                # O CONCEITO é o mesmo — instrução com autoridade sobre a conversa,
                # separada das falas. Só a embalagem muda.
                config=genai_types.GenerateContentConfig(
                    system_instruction=PROMPT_DE_SISTEMA,
                    max_output_tokens=self._max_tokens,
                    # DESLIGADO DE PROPÓSITO, e não é só para calar o aviso.
                    #
                    # "Automatic function calling" é o SDK EXECUTAR sozinho as
                    # funções Python que o modelo pedir, e devolver o resultado
                    # sem passar por você. Hoje é inofensivo — não registramos
                    # função nenhuma. Na Fase 2, com tools, seria o SDK abrindo
                    # um caminho LLM -> execução que pula o Policy Engine.
                    #
                    # Isso é exatamente o que o P3 proíbe: "o LLM pede, o
                    # sistema decide; nunca LLM -> shell". Desligar agora, com
                    # o motivo escrito, é mais barato que descobrir em fevereiro
                    # que existia uma porta dos fundos ligada desde agosto.
                    automatic_function_calling=(
                        genai_types.AutomaticFunctionCallingConfig(disable=True)
                    ),
                ),
            )
        except genai_errors.APIError as erro:
            # `APIError` é a base de ClientError (4xx) e ServerError (5xx) no
            # SDK do Google. Pegar a base cobre os dois — inclusive o 503 de
            # "modelo com muita demanda", que foi o erro que expôs este bug.
            raise FalhaDoProvider(f"Gemini: {erro}") from erro

        # --- Leitura da resposta, com a mesma disciplina do outro provider ---
        #
        # `finish_reason` é o equivalente do `stop_reason` da Anthropic: diz
        # POR QUE o modelo parou. Vale checar antes de confiar no conteúdo,
        # porque "parou porque terminou" (STOP) e "parou porque o filtro de
        # segurança barrou" (SAFETY) chegam com a mesma cara de sucesso.
        motivo = resposta.candidates[0].finish_reason if resposta.candidates else None

        # `.text` já concatena todos os pedaços de texto da resposta — mesmo
        # papel do nosso filtro por `bloco.type == "text"` no provider da
        # Anthropic, só que o SDK do Google já faz por você. Ele devolve `None`
        # quando não há texto nenhum, e é por isso que o `if` abaixo existe.
        texto = resposta.text

        if not texto:
            raise RespostaVazia(
                f"O Gemini respondeu sem texto (finish_reason={motivo}). "
                f"SAFETY ou PROHIBITED_CONTENT significam filtro de conteúdo; "
                f"MAX_TOKENS significa que o teto de {self._max_tokens} foi baixo demais."
            )

        return texto


async def listar_modelos_gemini(cliente: genai.Client | None = None) -> list[str]:
    """Nomes dos modelos Gemini disponíveis para a sua chave.

    Existe porque nome de modelo ENVELHECE. A constante `MODELO_GEMINI_PADRAO`
    lá em cima é um chute informado, não uma verdade eterna: modelos são
    lançados e aposentados, e descobrir isso por um 404 no meio de uma
    conversa é a pior hora possível.

    Mora neste arquivo, e não num utilitário à parte, por causa do P1 — o SDK
    do Google não pode ser importado em nenhum outro lugar do projeto. Quem
    quiser listar modelos chama esta função; ninguém fala com o Google direto.
    """
    cliente = cliente if cliente is not None else genai.Client()
    nomes: list[str] = []
    async for modelo in await cliente.aio.models.list():
        if modelo.name:
            nomes.append(modelo.name.removeprefix("models/"))
    return sorted(nomes)
