import os
import base64
import logging
from time import sleep
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Configuração do ambiente
load_dotenv()  # Carrega as variáveis 

# Configurações da OpenAI
cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = "gpt-4o-mini"

# Definição dos diretórios principais 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório base do script
DIR_SRC = os.path.dirname(BASE_DIR)  # Diretório src
DIR_PAI = os.path.dirname(DIR_SRC)  # Diretório pai
if DIR_PAI not in sys.path:
    sys.path.append(DIR_PAI)
DIR_DATA = os.path.join(DIR_PAI, "data")  # Diretório para armazenamento de dados
DIR_PDF_TO_IMAGE = os.path.join(DIR_DATA, "processed_pdf_to_images")  # Imagens processadas a partir de PDFs
DIR_VISION = os.path.join(DIR_DATA, "outputs_vision")  # Saída do processamento do Vision
DIR_LOGS =  os.path.join(DIR_DATA, "logs") # Diretório de logs

from src.utils.logging_config import log_config
logging = log_config(DIR_LOGS, "vision")

# Função para codificar imagens em Base64
def encodar_imagem(caminho_imagem):
    """Codifica uma imagem em Base64."""
    try:
        with open(caminho_imagem, "rb") as arquivo_imagem:
            return base64.b64encode(arquivo_imagem.read()).decode("utf-8")
    except Exception as e:
        logging.error(f"Erro ao codificar imagem {caminho_imagem}: {e}")
        return None

# Função para analisar a imagem
def analisar_imagem(caminho_imagem):
    """
    Analisa uma imagem usando o Vision da OpenAI.

    Args:
        caminho_imagem (str): Caminho completo para a imagem a ser analisada.

    Returns:
        tuple: Descrição do conteúdo analisado e custo fictício (retorna sempre 0).
    """
    logging.info(f"Iniciando análise da imagem: {caminho_imagem}")
    imagem_base64 = encodar_imagem(caminho_imagem)
    if not imagem_base64:
        return None, 0

    # Construção do prompt para análise da imagem
    prompt = f"""
    Analise o conteúdo técnico da imagem fornecida. Extraia e organize informações relevantes, incluindo:
    - Títulos, subtítulos e parágrafos.
    - Elementos visuais como gráficos, tabelas e diagramas.
    - Procedimentos e especificações técnicas.
    Seja claro, preciso e mantenha a hierarquia das informações.
    ,{imagem_base64}
    """

    try:
        resposta = cliente.chat.completions.create(
            model=modelo,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpg;base64,{imagem_base64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=600,
        )
        conteudo = resposta.choices[0].message.content
        logging.info("Análise concluída com sucesso.")
        return conteudo, 0  # Retorna a descrição e custo fictício (0 por enquanto)
    except Exception as e:
        logging.error(f"Erro ao processar a imagem {caminho_imagem}: {e}")
        return None, 0

# Função para salvar o resultado
def salvar_resultado(nome_do_arquivo, conteudo):
    """
    Salva o conteúdo da análise em um arquivo de texto.

    Args:
        nome_do_arquivo (str): Caminho completo do arquivo onde o conteúdo será salvo.
        conteudo (str): Texto a ser salvo no arquivo.
    """
    try:
        with open(nome_do_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        logging.info(f"Resultado salvo em {nome_do_arquivo}")
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo {nome_do_arquivo}: {e}")

# Função principal
if __name__ == "__main__":
    total_custo = 0  # Controle de custo fictício (não utilizado neste script)

    logging.info("Início do processamento de imagens para análise.")
    try:
        # Itera por todas as subpastas em DIR_PDF_TO_IMAGE
        for subpasta in os.listdir(DIR_PDF_TO_IMAGE):
            subpasta_path = os.path.join(DIR_PDF_TO_IMAGE, subpasta)
            if os.path.isdir(subpasta_path):  # Verifica se o caminho é uma pasta
                logging.info(f"Processando subpasta: {subpasta}")

                # Cria a pasta correspondente em DIR_VISION, se não existir
                vision_output_path = os.path.join(DIR_VISION, subpasta)
                os.makedirs(vision_output_path, exist_ok=True)

                # Itera por todos os arquivos de imagem na subpasta
                for arquivo in os.listdir(subpasta_path):
                    if arquivo.lower().endswith((".jpg", ".jpeg", ".png")):
                        caminho_imagem = os.path.join(subpasta_path, arquivo)
                        try:
                            # Processa a imagem e salva o resultado
                            descricao, _ = analisar_imagem(caminho_imagem)
                            if descricao:
                                nome_do_arquivo = os.path.join(
                                    vision_output_path, 
                                    f"{os.path.splitext(arquivo)[0]}_description.txt"
                                )
                                salvar_resultado(nome_do_arquivo, descricao)
                        except Exception as e:
                            logging.error(f"Erro no processamento da imagem {arquivo}: {e}")
                        sleep(1)  # Aguarda para respeitar limites de requisição
    except Exception as e:
        logging.critical(f"Erro crítico durante o processamento: {e}")

    logging.info("Processamento concluído.")