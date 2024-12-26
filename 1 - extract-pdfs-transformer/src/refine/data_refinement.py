import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Configurações do OpenAI
cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = "gpt-4o-mini"

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório base do script
DIR_SRC = os.path.dirname(BASE_DIR) # Diretório src
DIR_PAI = os.path.dirname(DIR_SRC)  # Diretório pai
if DIR_PAI not in sys.path:
    sys.path.append(DIR_PAI)  # Adiciona o diretório pai ao PATH do sistema
DIR_DATA = os.path.join(DIR_PAI, "data")  # Diretório para armazenamento de dados
DIR_VISION = os.path.join(DIR_DATA, "outputs_vision")  # Diretório para arquivos de visão
DIR_DATA_PROCESSED_CLEAN = os.path.join(DIR_DATA, "processed_clean")  # Diretório para arquivos limpos
DIR_DATA_REFINEMENT = os.path.join(DIR_DATA, "outputs_vision_and_extractor")  # Diretório de refinamento
DIR_LOGS = os.path.join(DIR_DATA, "logs")  # Diretório para logs

# Configuração de logging
from src.utils.logging_config import log_config
logging = log_config(DIR_LOGS, "data_refinement")  # Nome do arquivo de log: data_refinement.log


# Função para carregar um arquivo JSON
def carregar_json(caminho_json):
    """
    Carrega um arquivo JSON e retorna seu conteúdo.

    Args:
        caminho_json (str): Caminho para o arquivo JSON.

    Returns:
        dict: Conteúdo do arquivo JSON.
    """
    try:
        with open(caminho_json, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except Exception as e:
        logging.error(f"Erro ao carregar JSON {caminho_json}: {e}")
        return None


# Função para carregar um arquivo TXT
def carregar_txt(caminho_txt):
    """
    Carrega um arquivo TXT e retorna seu conteúdo como string.

    Args:
        caminho_txt (str): Caminho para o arquivo TXT.

    Returns:
        str: Conteúdo do arquivo TXT.
    """
    try:
        with open(caminho_txt, "r", encoding="utf-8") as arquivo:
            return arquivo.read()
    except Exception as e:
        logging.error(f"Erro ao carregar TXT {caminho_txt}: {e}")
        return None


# Função para enviar um prompt para o OpenAI
def enviar_para_openai(contexto, descricao_txt):
    """
    Envia um prompt para o OpenAI e retorna a resposta gerada.

    Args:
        contexto (str): Conteúdo do arquivo JSON.
        descricao_txt (str): Conteúdo do arquivo TXT.

    Returns:
        str: Resposta gerada pelo OpenAI.
    """
    prompt = f"""
Você recebeu informações de dois formatos diferentes de arquivos sobre um mesmo conteúdo para analisar e unificar. 
Use os detalhes fornecidos no contexto (JSON) e na descrição do arquivo de visão (TXT). 
Combine as informações, elimine redundâncias, preencha lacunas e organize em formato claro e hierárquico. 
Preciso de um documento unificado com todas as informações técnicas disponíveis e suas unidades. 
**Descreva apenas com o conteúdo técnico necessário, seja objetivo e não faça nenhuma avaliação pessoal**

### Contexto JSON:
{contexto}

### Descrição TXT:
{descricao_txt}

Gere uma resposta detalhada e unificada das informações técnicas descritas nos documentos.
    """
    
    sistema = {
        "temperature": 0.3,
        "max_tokens": 1000,
        "top_p": 1
    }
    
    try:
        resposta = cliente.chat.completions.create(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            **sistema,
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Erro ao acessar a OpenAI: {e}")
        return None


# Função principal para processar os arquivos
def processar_arquivos():
    """
    Processa os arquivos JSON e TXT, unificando informações e salvando os resultados.
    """
    # Cria o diretório de refinamento, se não existir
    os.makedirs(DIR_DATA_REFINEMENT, exist_ok=True)

    # Lista todos os arquivos JSON no diretório de entrada
    arquivos_json = [f for f in os.listdir(DIR_DATA_PROCESSED_CLEAN) if f.endswith(".json")]

    for arquivo_json in arquivos_json:
        caminho_json = os.path.join(DIR_DATA_PROCESSED_CLEAN, arquivo_json)
        json_data = carregar_json(caminho_json)

        # Verifica se o JSON foi carregado com sucesso
        if not json_data:
            logging.warning(f"Pular arquivo {arquivo_json} devido a erro no carregamento.")
            continue

        base_nome = os.path.splitext(arquivo_json)[0]
        subpasta_txt = os.path.join(DIR_VISION, base_nome)
        subpasta_saida = os.path.join(DIR_DATA_REFINEMENT, base_nome)

        # Cria a subpasta de saída correspondente
        os.makedirs(subpasta_saida, exist_ok=True)

        # Verifica se a subpasta de TXT existe
        if not os.path.exists(subpasta_txt):
            logging.warning(f"Subpasta correspondente não encontrada: {subpasta_txt}")
            continue

        # Itera pelas páginas no JSON
        for pagina in json_data:
            numero_pagina = pagina["page"]
            nome_txt = f"{base_nome}_pag{numero_pagina}_description.txt"
            caminho_txt = os.path.join(subpasta_txt, nome_txt)

            # Verifica se o arquivo TXT da página existe
            if os.path.exists(caminho_txt):
                txt_data = carregar_txt(caminho_txt)

                if txt_data:
                    resposta_openai = enviar_para_openai(pagina["text"], txt_data)

                    # Salva a resposta na subpasta correspondente
                    if resposta_openai:
                        saida_arquivo = os.path.join(subpasta_saida, f"{base_nome}_pag{numero_pagina}_resultado.json")
                        try:
                            with open(saida_arquivo, "w", encoding="utf-8") as saida:
                                json.dump(
                                    {"page": numero_pagina, "unified_analysis": resposta_openai},
                                    saida,
                                    ensure_ascii=False,
                                    indent=4
                                )
                            logging.info(f"Resultado salvo em: {saida_arquivo}")
                        except Exception as e:
                            logging.error(f"Erro ao salvar resultado em {saida_arquivo}: {e}")
                else:
                    logging.warning(f"Dados TXT para página {numero_pagina} não carregados.")
            else:
                logging.warning(f"Arquivo TXT para página {numero_pagina} não encontrado: {nome_txt}")


# Ponto de entrada principal
if __name__ == "__main__":
    logging.info("Início do processamento de arquivos.")
    try:
        processar_arquivos()
    except Exception as e:
        logging.critical(f"Erro crítico durante o processamento: {e}")
    logging.info("Processamento concluído.")