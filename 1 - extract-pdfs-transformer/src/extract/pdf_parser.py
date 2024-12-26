import fitz  # PyMuPDF
import pytesseract
from pytesseract import Output
from PIL import Image
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Diretório base do script
DIR_SRC = os.path.dirname(BASE_DIR) # Diretório src
DIR_PAI = os.path.dirname(DIR_SRC) # Diretório pai 
if DIR_PAI not in sys.path: # Adicionando o diretório pai no path do script
    sys.path.append(DIR_PAI) # Diretório dos PDFs
DIR_DATA = os.path.join(DIR_PAI, "data") # Diretório para armazenamento de dados
DIR_DATA_RAW = os.path.join(DIR_DATA, "raw") 
DIR_DATA_PROCESSED =  os.path.join(DIR_DATA, "processed") # Diretório dos dados extraídos dos PDFs (pymu)
DIR_LOGS =  os.path.join(DIR_DATA, "logs") # Diretório de logs

from src.utils.logging_config import log_config
logging = log_config(DIR_LOGS, "pdf_parser")

def extract_text_from_pdf(pdf_path):
    """
    Extrai texto de um PDF. Usa PyMuPDF para PDFs pesquisáveis e Tesseract OCR para imagens.

    Args:
        pdf_path (str): Caminho para o arquivo PDF.

    Returns:
        list: Lista de dicionários contendo número da página e texto extraído.
    """
    logging.info(f"Iniciando extração de texto para {pdf_path}")
    pdf_document = fitz.open(pdf_path)
    extracted_data = []

    for page_num in range(len(pdf_document)):
        try:
            page = pdf_document[page_num]
            text = page.get_text("text")  # Extrai texto pesquisável

            # Verifica se a página possui texto extraível
            if not text.strip():
                logging.info(f"Página {page_num + 1} sem texto. Aplicando OCR...")
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang="por", output_type=Output.STRING)

            extracted_data.append({
                "page": page_num + 1,
                "text": text.strip()
            })
        except Exception as e:
            logging.error(f"Erro ao processar a página {page_num + 1} do arquivo {pdf_path}: {e}")
            extracted_data.append({
                "page": page_num + 1,
                "text": "",
                "error": str(e)
            })

    pdf_document.close()
    logging.info(f"Extração concluída para {pdf_path}")
    return extracted_data

def save_as_json(data, output_path):
    """
    Salva os dados extraídos em formato JSON.

    Args:
        data (list): Dados extraídos do PDF.
        output_path (str): Caminho para salvar o arquivo JSON.
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Dados extraídos salvos em {output_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar arquivo JSON em {output_path}: {e}")

if __name__ == "__main__":
    # Configuração de diretórios
    input_dir = DIR_DATA_RAW
    output_dir = DIR_DATA_PROCESSED
    os.makedirs(output_dir, exist_ok=True)

    for pdf_file in os.listdir(input_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, pdf_file)
            output_path = os.path.join(output_dir, pdf_file.replace(".pdf", ".json"))

            try:
                logging.info(f"Processando arquivo {pdf_file}...")
                extracted_data = extract_text_from_pdf(pdf_path)
                save_as_json(extracted_data, output_path)
            except Exception as e:
                logging.error(f"Erro ao processar {pdf_file}: {e}")