"""Onde a conversa fica quando o programa não está rodando.

O critério de saída da Fase 0 é exatamente isto: conversar, fechar, reabrir e
ela lembrar. Este módulo é a única peça que toca o disco.

Ele NÃO sabe conversar e NÃO sabe chamar API. Ele sabe pegar uma `Conversa` e
transformá-la em bytes, e o contrário. Só isso.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from friday.models import Conversa


class ArquivoDeConversaCorrompido(Exception):
    """O arquivo existe, mas não é uma `Conversa` válida.

    Existe como exceção própria para que o `main.py` possa distinguir "nunca
    houve conversa" (arquivo ausente — normal, é a primeira execução) de "havia
    uma conversa e ela está ilegível" (grave). São situações opostas e não
    podem virar o mesmo `except`.
    """


class ConversationStore(Protocol):
    """O contrato: o que qualquer lugar de guardar conversa precisa saber fazer.

    É um `Protocol`, não uma classe-base. A diferença importa:

    Com herança (`class JSONStore(ConversationStore)`), a implementação precisa
    *saber que este arquivo existe* e importá-lo. Com `Protocol`, ela só
    precisa ter os métodos com as assinaturas certas — o mypy confere o encaixe
    sozinho, sem que ninguém herde nada. É o "se anda como pato e grasna como
    pato" do Python, só que verificado antes de rodar em vez de descoberto em
    produção.

    Por que isso aqui: o ADR-002 (qual banco usar) está EM ABERTO, e será
    decidido lá no mês 5, com repertório. Enquanto isso, JSON num arquivo. Esta
    interface é o que garante que trocar depois seja barato — no dia em que
    existir um `PostgresConversationStore`, nada fora deste módulo muda, porque
    ninguém fora daqui conhece qualquer implementação concreta.

    Os métodos são `async` por causa do ADR-001 (asyncio é o modelo de
    concorrência do projeto). Ler um arquivo local não precisa disso hoje. Mas
    o ADR-006 manda desenhar a fronteira como se ela já fosse rede — e no dia
    em que o store estiver do outro lado de um socket, a assinatura já está
    certa e nenhum chamador precisa mudar de cor.
    """

    async def carregar(self) -> Conversa:
        """Devolve a conversa gravada, ou uma nova e vazia se não houver nenhuma."""
        ...

    async def salvar(self, conversa: Conversa) -> None:
        """Grava o estado atual, substituindo o anterior por inteiro."""
        ...


class JSONConversationStore:
    """Guarda a conversa num único arquivo `.json`, legível a olho nu.

    Legível a olho nu é uma escolha, não acaso: na Fase 0 o modo mais provável
    de depurar um problema é abrir o arquivo e olhar. Um formato binário
    economizaria bytes e custaria a única ferramenta de diagnóstico que existe
    hoje.
    """

    def __init__(self, caminho: Path) -> None:
        self._caminho = caminho

    # ------------------------------------------------------------------
    # A parte assíncrona é uma casca fina. O trabalho real é síncrono, nos
    # métodos `_sync` abaixo, e roda numa thread separada via `asyncio.to_thread`.
    #
    # Por quê: `open()` e `write()` BLOQUEIAM. Dentro de um programa asyncio,
    # uma chamada bloqueante trava o event loop inteiro — nada mais roda até
    # ela terminar, incluindo coisas que nada têm a ver com disco. `to_thread`
    # empurra a chamada bloqueante para uma thread e devolve o controle ao loop
    # enquanto ela acontece.
    #
    # Com um arquivo pequeno e local isso é irrelevante na prática. Está aqui
    # porque o hábito de misturar chamada bloqueante em código async é o tipo
    # de erro que não dá sintoma nenhum até o dia em que dá, e aí o sintoma é
    # "o programa inteiro congela de vez em quando" — quase impossível de achar.
    # ------------------------------------------------------------------

    async def carregar(self) -> Conversa:
        return await asyncio.to_thread(self._carregar_sync)

    async def salvar(self, conversa: Conversa) -> None:
        await asyncio.to_thread(self._salvar_sync, conversa)

    def _carregar_sync(self) -> Conversa:
        try:
            bruto = self._caminho.read_bytes()
        except FileNotFoundError:
            # Primeira execução na máquina. Não é erro: é o começo.
            return Conversa()

        try:
            # `model_validate_json` valida NA ENTRADA. Um JSON com `role`
            # inválido, ou com timestamp sem fuso, é recusado aqui — na
            # fronteira — e não três camadas adiante, onde o erro não teria
            # mais relação visível com o arquivo que o causou.
            return Conversa.model_validate_json(bruto)
        except (ValidationError, ValueError) as erro:
            # Deixar explodir é deliberado. A alternativa tentadora é
            # `return Conversa()` — "deu ruim, começa do zero". Isso apagaria a
            # memória dela em silêncio, que é o pior modo de falha possível
            # num projeto cujo ponto inteiro é lembrar. Melhor parar e gritar:
            # o arquivo ainda está lá, intacto, e dá para consertar à mão.
            raise ArquivoDeConversaCorrompido(
                f"{self._caminho} existe mas não é uma Conversa válida. "
                f"O arquivo NÃO foi alterado — abra e inspecione antes de apagar."
            ) from erro

    def _salvar_sync(self, conversa: Conversa) -> None:
        self._caminho.parent.mkdir(parents=True, exist_ok=True)

        conteudo = conversa.model_dump_json(indent=2)

        # ESCRITA ATÔMICA — e aqui está a parte que mais importa neste arquivo.
        #
        # O jeito ingênuo é abrir o arquivo final e escrever nele. O problema:
        # abrir para escrita ZERA o arquivo antes de escrever o conteúdo novo.
        # Se o programa morrer nesse intervalo — Ctrl+C, falta de luz, disco
        # cheio — o que sobra é um arquivo pela metade, ou vazio. A conversa
        # inteira, perdida.
        #
        # E o critério de saída da Fase 0 é LITERALMENTE apertar Ctrl+C. Então
        # a janela de risco não é teórica aqui, é o fluxo de uso normal.
        #
        # A solução: escrever num arquivo temporário e depois RENOMEAR por cima
        # do definitivo. `os.replace` é atômico no sistema de arquivos — em
        # qualquer instante, o caminho final aponta ou para o conteúdo velho
        # inteiro, ou para o novo inteiro. Nunca para um meio-termo.
        #
        # O temporário precisa nascer no MESMO diretório do destino: renomear
        # só é atômico dentro do mesmo volume. Um temporário em C:\Temp com
        # destino em D:\ viraria uma cópia, que tem exatamente o problema que
        # estamos evitando.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self._caminho.parent,
            prefix=f"{self._caminho.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporario:
            temporario.write(conteudo)
            # `flush` empurra do buffer do Python para o sistema operacional;
            # `fsync` empurra do sistema operacional para o disco de verdade.
            # Sem os dois, o `replace` abaixo pode publicar um arquivo cujo
            # conteúdo ainda está em cache e some numa queda de energia.
            temporario.flush()
            os.fsync(temporario.fileno())
            caminho_temporario = Path(temporario.name)

        os.replace(caminho_temporario, self._caminho)
