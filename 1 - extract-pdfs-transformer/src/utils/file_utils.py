import os

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório base do script
DIR_SRC = os.path.dirname(BASE_DIR)  # Diretório src
DIR_PAI = os.path.dirname(DIR_SRC)  # Diretório pai                 
DIR_DATA = os.path.join(DIR_PAI, "data")  # Diretório para armazenamento de dados
DIR_LOGS =  os.path.join(DIR_DATA, "logs") # Diretório de logs
DIR_DATA_RAW = os.path.join(DIR_DATA, "raw") # Diretório dos PDFs
DIR_DATA_PROCESSED =  os.path.join(DIR_DATA, "processed") # Diretório dos dados extraídos dos PDFs (pymu)
DIR_DATA_PROCESSED_CLEAN =  os.path.join(DIR_DATA, "processed_clean") # Diretório dos dados limpos de copyright
DIR_PDF_TO_IMAGE = os.path.join(DIR_DATA, "processed_pdf_to_images")  # Diretório de  imagens processadas a partir de PDFs
DIR_VISION = os.path.join(DIR_DATA, "outputs_vision")  # Diretório de saída do processamento do Vision
DIR_DATA_REFINEMENT =  os.path.join(DIR_DATA, "outputs_vision_and_extractor") # Diretório de refinamento dos dados (Vision + pymu)
DIR_SUMMARIES = os.path.join(DIR_DATA, "outputs_final_summaries")  # Diretório para salvar sumários finais

# Função de criação de diretórios principais
def cria_diretorios():
    os.makedirs(DIR_DATA, exist_ok=True)
    os.makedirs(DIR_LOGS, exist_ok=True)
    os.makedirs(DIR_DATA_RAW, exist_ok=True)
    os.makedirs(DIR_DATA_PROCESSED, exist_ok=True)
    os.makedirs(DIR_DATA_PROCESSED_CLEAN, exist_ok=True)
    os.makedirs(DIR_PDF_TO_IMAGE, exist_ok=True)
    os.makedirs(DIR_VISION, exist_ok=True)
    os.makedirs(DIR_DATA_REFINEMENT, exist_ok=True)
    os.makedirs(DIR_SUMMARIES, exist_ok=True)