import os
import json
import re
import sys

# Diretórios principais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # Diretório atual
DIR_SRC = os.path.dirname(BASE_DIR)  # Diretório src
DIR_PAI = os.path.dirname(DIR_SRC)  # Diretório pai
if DIR_PAI not in sys.path: # Adicionando o diretório pai no path do script
    sys.path.append(DIR_PAI) # Diretório dos PDFs
DIR_DATA = os.path.join(DIR_PAI, "data")  # Diretório de dados
DIR_DATA_RAW = os.path.join(DIR_DATA, "raw")  # Diretório para dados brutos
DIR_DATA_PROCESSED = os.path.join(DIR_DATA, "processed")  # Diretório para dados processados
DIR_DATA_PROCESSED_CLEAN = os.path.join(DIR_DATA, "processed_clean")  # Diretório para dados processados e limpos
DIR_LOGS =  os.path.join(DIR_DATA, "logs") # Diretório de logs

from src.utils.logging_config import log_config
logging = log_config(DIR_LOGS, "process_clean")

# Lista de padrões abrangendo variações da frase
frases_a_remover = [
    r"e o contrato de licença de uso.*?Doutor-IE Online",
    r"Esta página é parte integrante da Enciclopédia Automotiva.*?Doutor-IE Online",
    r"Reprodução, distribuição, compartilhamento e comercialização são proibidas.*?Lei dos Direitos Autorais.*?",
    r"Denuncie a cópia fraudulenta pelo fone.*?direitos reservados\.",
    r"\(lei 9610/1998\)",
    r"\ne o contrato de licença de uso.",
    r"\nEsta página é parte integrante da Plataforma Doutor-IE."
]

def limpar_texto(texto, frases):
    """
    Remove frases indesejadas do texto usando regex.

    Args:
        texto (str): Texto a ser limpo.
        frases (list): Lista de padrões regex a serem removidos.

    Returns:
        str: Texto limpo.
    """
    try:
        for frase in frases:
            texto = re.sub(frase, '', texto, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
        return texto.strip()
    except Exception as e:
        logging.error(f"Erro ao limpar texto: {e}")
        return texto

# Processamento dos arquivos
def processar_arquivos():
    """
    Processa os arquivos JSON no diretório DIR_DATA_PROCESSED, limpa o texto e salva no diretório DIR_DATA_PROCESSED_CLEAN.
    """
    arquivos = [f for f in os.listdir(DIR_DATA_PROCESSED) if f.endswith(".json")]
    if not arquivos:
        logging.warning("Nenhum arquivo JSON encontrado para processar.")
        return

    for arquivo_nome in arquivos:
        caminho_completo_entrada = os.path.join(DIR_DATA_PROCESSED, arquivo_nome)
        caminho_completo_saida = os.path.join(DIR_DATA_PROCESSED_CLEAN, arquivo_nome)

        try:
            # Abrir e carregar o arquivo JSON
            with open(caminho_completo_entrada, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            # Processar cada página
            for pagina in dados:
                if "text" in pagina:
                    texto_original = pagina["text"]
                    texto_limpo = limpar_texto(texto_original, frases_a_remover)
                    pagina["text"] = texto_limpo

            # Salvar o arquivo JSON processado no diretório de saída
            with open(caminho_completo_saida, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=4)
            
            logging.info(f"Arquivo processado com sucesso: {arquivo_nome}")

        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON {arquivo_nome}: {e}")
        except Exception as e:
            logging.error(f"Erro ao processar arquivo {arquivo_nome}: {e}")

if __name__ == "__main__":
    logging.info("Início do processamento de limpeza de dados.")
    try:
        processar_arquivos()
    except Exception as e:
        logging.critical(f"Erro crítico durante o processamento: {e}")
    logging.info(f"Processamento concluído. Arquivos salvos em: {DIR_DATA_PROCESSED_CLEAN}")