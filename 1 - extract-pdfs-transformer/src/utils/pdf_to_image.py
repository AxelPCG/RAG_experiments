import fitz  # PyMuPDF
from PIL import Image
import os
import logging
import sys

# Definição de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório base onde o script está sendo executado
DIR_SRC = os.path.dirname(BASE_DIR)  # Diretório src
DIR_PAI = os.path.dirname(DIR_SRC)  # Diretório pai
if DIR_PAI not in sys.path:
    sys.path.append(DIR_PAI)
DIR_DATA = os.path.join(DIR_PAI, "data")  # Diretório principal de dados
DIR_DATA_RAW = os.path.join(DIR_DATA, "raw")  # Diretório para arquivos PDF brutos
DIR_PDF_TO_IMAGE = os.path.join(DIR_DATA, "processed_pdf_to_images")  # Diretório para saída de imagens
DIR_LOGS =  os.path.join(DIR_DATA, "logs") # Diretório de logs

from src.utils.logging_config import log_config
logging = log_config(DIR_LOGS, "pdf_to_image")

def pdf_to_image(pdf_path, output_dir):
    """
    Converte todas as páginas de um arquivo PDF para imagens no formato .jpg.

    Args:
        pdf_path (str): Caminho completo do arquivo PDF.
        output_dir (str): Caminho do diretório onde as imagens serão salvas.

    Returns:
        None
    """
    try:
        logging.info(f"Iniciando processamento do PDF: {pdf_path}")
        pdf_document = fitz.open(pdf_path)  # Abre o arquivo PDF
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]  # Extrai o nome do PDF sem extensão
        num_pages = len(pdf_document)  # Conta o número de páginas no PDF

        for page_num in range(num_pages):
            try:
                # Processa cada página do PDF
                page = pdf_document[page_num]
                pix = page.get_pixmap()  # Gera a imagem da página
                
                # Converte para imagem RGB e salva como .jpg
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                output_file = os.path.join(output_dir, f"{pdf_name}_pag{page_num + 1}.jpg")
                img.save(output_file, "JPEG")
                
                logging.info(f"Página {page_num + 1}/{num_pages} salva em {output_file}")
            except Exception as page_error:
                # Registra erro ao processar uma página específica
                logging.error(f"Erro ao processar a página {page_num + 1}: {page_error}")

        pdf_document.close()  # Fecha o arquivo PDF
        logging.info(f"Processamento concluído para o PDF: {pdf_path}")
    except Exception as pdf_error:
        # Registra erro ao abrir ou processar o PDF
        logging.error(f"Erro ao abrir ou processar o PDF {pdf_path}: {pdf_error}")

if __name__ == "__main__":
    # Itera sobre todos os arquivos na pasta de entrada
    for pdf_file in os.listdir(DIR_DATA_RAW):
        if pdf_file.lower().endswith(".pdf"):  # Processa apenas arquivos com extensão .pdf
            pdf_path = os.path.join(DIR_DATA_RAW, pdf_file)  # Caminho completo do arquivo PDF
            pdf_output_dir = os.path.join(DIR_PDF_TO_IMAGE, os.path.splitext(pdf_file)[0])  # Diretório de saída específico para o PDF
            os.makedirs(pdf_output_dir, exist_ok=True)  # Cria o diretório de saída, se necessário

            try:
                pdf_to_image(pdf_path, pdf_output_dir)  # Chama a função de conversão
            except Exception as e:
                # Registra erro ao processar um arquivo PDF específico
                logging.error(f"Erro ao processar o arquivo {pdf_file}: {e}")