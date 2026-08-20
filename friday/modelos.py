"""Lista os modelos disponíveis para a sua chave.

    python -m friday.modelos

Repare que este arquivo NÃO importa o SDK do Google — ele chama uma função do
`friday.llm`, que é o único lugar autorizado a isso (P1). A regra não é
decoração: é ela que garante que trocar de provider um dia seja mexer em um
arquivo, e não caçar imports pelo projeto.
"""

import asyncio

from dotenv import load_dotenv

from friday.llm import listar_modelos_gemini


async def main() -> None:
    load_dotenv()
    for nome in await listar_modelos_gemini():
        print(nome)


if __name__ == "__main__":
    asyncio.run(main())
