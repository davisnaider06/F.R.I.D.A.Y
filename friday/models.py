"""Vocabulário de dados da Sexta-Feira.

Este módulo não conversa, não salva e não chama API. Ele só define *o que as
coisas são*. Todo o resto (`llm.py`, `store.py`, `main.py`) depende daqui, e
este arquivo não depende de nenhum deles — é o que impede o formato interno de
nascer moldado pelo formato que a API da Anthropic espera hoje (P1).
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


def _novo_id() -> str:
    """Identificador único de mensagem.

    `uuid4` é aleatório puro. Existe `uuid7` (ordenável por tempo), mas ele
    exige Python 3.14+ e o ADR-001 declara 3.12+ — e como já gravamos o
    `timestamp` explicitamente, a ordenação embutida seria redundante.
    """
    return str(uuid4())


def _agora_utc() -> datetime:
    """O instante atual, COM fuso, sempre em UTC.

    Nunca `datetime.now()` sozinho: um datetime sem fuso é um número sem
    unidade — não dá pra saber que instante ele representa, e o Python se
    recusa a compará-lo com um datetime que tem fuso (`TypeError`).
    Guardamos em UTC; converter para o fuso local é problema de quem exibe.
    """
    return datetime.now(UTC)


class Mensagem(BaseModel):
    """Uma fala na conversa — sua ou dela.

    É um registro histórico: aconteceu, e não muda mais. Daí `frozen=True`
    logo abaixo, que faz o pydantic recusar qualquer tentativa de alterar um
    campo depois de criado. Reescrever uma mensagem antiga não é atualização,
    é falsificação de histórico; melhor que o erro apareça na linha que tentou
    fazer isso do que numa conversa estranha três semanas depois.
    """

    model_config = ConfigDict(frozen=True)

    # `default_factory` recebe a FUNÇÃO, não o resultado dela.
    # Com `= _novo_id()` o Python executaria a chamada uma única vez, ao
    # importar o módulo, e guardaria aquele valor como padrão — toda mensagem
    # da execução inteira nasceria com o mesmo id. Assim, o pydantic chama a
    # função de novo a cada mensagem criada.
    id: str = Field(default_factory=_novo_id)

    # `Literal` aceita SÓ estes dois valores. Com `str` puro, um "usuário" com
    # acento seria aceito aqui e só explodiria lá na chamada HTTP, com uma
    # mensagem de erro que não menciona typo nenhum. A regra geral do projeto:
    # tornar o estado inválido impossível de construir, em vez de conferir
    # depois se ele é válido.
    role: Literal["user", "assistant"]

    # Texto puro por enquanto. Dívida registrada: quando entrarem tools
    # (Fase 2), o conteúdo vira uma lista de blocos — texto, pedido de tool,
    # resultado de tool. Adivinhar esse formato agora, sem nunca ter escrito
    # uma tool, produziria a abstração errada; prefiro pagar a migração depois.
    content: str

    # `AwareDatetime` (e não `datetime`) faz o pydantic REJEITAR um horário sem
    # fuso na fronteira — inclusive um vindo de um JSON antigo no disco. Não é
    # só documentação, é uma trava.
    #
    # Semântica: é o instante em que este objeto foi construído no nosso
    # processo. Para uma mensagem sua, quando você apertou Enter; para uma dela,
    # quando recebemos a resposta. NÃO é quando o modelo gerou os tokens nem o
    # horário do servidor da Anthropic.
    timestamp: AwareDatetime = Field(default_factory=_agora_utc)


class Conversa(BaseModel):
    """A linha do tempo contínua entre você e a Sexta.

    Existe UMA conversa, e ela nunca termina. Abrir o programa é continuar de
    onde parou, não abrir uma sessão nova — é isso que separa "entidade
    contínua" de "chatbot com sessões".

    Mesmo assim ela carrega um `id`. Custa um campo hoje e é o que permite
    existirem várias um dia sem trocar o formato no disco nem migrar arquivo
    antigo.

    Ao contrário da `Mensagem`, esta classe NÃO é `frozen`: uma mensagem é
    registro histórico que congela; uma conversa é uma entidade viva que cresce.
    """

    # `frozen` aqui é no CAMPO, não no modelo inteiro: a conversa muda (ganha
    # mensagens), mas a identidade dela não. Um objeto que troca de id no meio
    # do caminho não é o mesmo objeto.
    id: str = Field(default_factory=_novo_id, frozen=True)

    # `default_factory=list`, não `= []`. Neste caso específico o pydantic te
    # protegeria dos dois jeitos (ele copia defaults mutáveis antes de
    # entregar), mas em Python puro `= []` é a armadilha clássica: a lista
    # nasceria uma vez só, no import, e TODA conversa compartilharia a mesma.
    # Escrever `default_factory` deixa a intenção explícita e não depende do
    # pydantic ser esperto por você.
    mensagens: list[Mensagem] = Field(default_factory=list)

    def adicionar(self, mensagem: Mensagem) -> None:
        """Acrescenta uma fala ao fim da linha do tempo.

        Muda o objeto no lugar e não devolve nada, de propósito. A alternativa
        (devolver uma `Conversa` nova) é mais segura sob concorrência, mas tem
        o modo de falha pior hoje: esquecer o `conversa = ` na chamada faria a
        mensagem sumir sem erro nenhum.

        O que torna essa escolha barata de reverter: ninguém fora daqui toca em
        `mensagens` direto. Toda mutação passa por este método. Se na Fase 5
        (ADR-006, "sem estado compartilhado") a imutabilidade virar necessária,
        muda-se aqui — e só aqui.
        """
        self.mensagens.append(mensagem)
