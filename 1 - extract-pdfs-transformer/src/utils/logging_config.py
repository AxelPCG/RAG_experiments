import logging

def log_config(log_path, doc_name):
    # Configuração de logging
    logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Logs no console
        logging.FileHandler(f"{log_path}\\{doc_name}.log")  # Logs em arquivo
    ]
    )
    return logging