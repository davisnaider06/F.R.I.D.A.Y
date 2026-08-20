
import os
from google import genai
from google.genai import types

client = genai.Client()

# 1. As "Mãos": A função que realmente roda na sua máquina
def listar_arquivos(diretorio: str = ".") -> list[str]:
    """Lista os arquivos de um diretório no sistema local do usuário.
    
    Args:
        diretorio: O caminho da pasta a ser listada. Padrão é a pasta atual.
    """
    try:
        return os.listdir(diretorio)
    except Exception as e:
        return [f"Erro ao acessar diretório: {e}"]

# 2. Registrando a ferramenta no modelo
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Quais arquivos eu tenho na minha pasta atual?",
    config=types.GenerateContentConfig(
        tools=[listar_arquivos] # Passamos a função como ferramenta
    )
)

# 3. O Gemini identifica que precisa da ferramenta e gera a chamada
print(response.function_calls)
