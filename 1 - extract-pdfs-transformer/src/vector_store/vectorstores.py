import os
import json
import pandas as pd
import itertools
from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv
import sys

# Diretórios principais
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Diretório base do script
DIR_SRC = os.path.dirname(BASE_DIR) # Diretório src
DIR_PAI = os.path.dirname(DIR_SRC) # Diretório pai 
if DIR_PAI not in sys.path: # Adicionando o diretório pai no path do script
    sys.path.append(DIR_PAI) # Diretório dos PDFs
DIR_DATA = os.path.join(DIR_PAI, "data")  # Diretório de dados
DIR_DATA_RAW = os.path.join(DIR_DATA, "raw")  # Diretório para dados brutos
DIR_LOGS = os.path.join(DIR_DATA, "logs")  # Diretório de logs
DIR_DATA_REFINEMENT = os.path.join(DIR_DATA, "outputs_vision_and_extractor")  # Diretório de refinamento


class CollectionCreator:
    def __init__(self, config_file: str):
        self.config = self.load_config(config_file)
        load_dotenv()
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not self.qdrant_url or not self.qdrant_api_key:
            raise ValueError("Variáveis QDRANT_URL ou QDRANT_API_KEY não encontradas!")

        self.file_to_metadata = self.load_metadata_from_csv()

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Carrega o arquivo de configuração JSON."""
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_metadata_from_csv(self) -> Dict[str, Dict[str, Any]]:
        """Carrega o CSV e cria um mapeamento arquivo_id -> metadados."""
        csv_path = os.path.join(DIR_DATA, "subcategoria_name.csv")
        df = pd.read_csv(csv_path)
        metadata_dict = df.set_index("arquivo_id").to_dict(orient="index")
        print("Metadados carregados do CSV:", metadata_dict)
        return metadata_dict

    def load_json_documents(self, file_id: str) -> List[Document]:
        """Carrega arquivos JSON, adiciona metadados do CSV e páginas."""
        dir_path = os.path.join(self.config['pdf_dir'], file_id)

        if not os.path.isdir(dir_path):
            print(f"Diretório {dir_path} não existe. Pulando.")
            return []

        documents = []
        for fname in os.listdir(dir_path):
            if fname.endswith("_resultado.json"):
                fpath = os.path.join(dir_path, fname)
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                text = data.get("unified_analysis", "")
                page_number = data.get("page", None)
                metadata = {
                    "source": fname,
                    "pag": page_number
                }

                try:
                    arquivo_id = int(fname.split("_")[1])  # Extrai arquivo_id do nome do arquivo
                    metadata["arquivo_id"] = arquivo_id
                    if arquivo_id in self.file_to_metadata:
                        csv_metadata = self.file_to_metadata[arquivo_id]
                        metadata.update(csv_metadata)
                    else:
                        print(f"Nenhum metadado encontrado para arquivo_id {arquivo_id}")
                except (IndexError, ValueError):
                    print(f"Erro ao extrair arquivo_id de {fname}")

                print("Metadados finais para o documento:", metadata)
                documents.append(Document(page_content=text, metadata=metadata))

        return documents

    def clean_metadata(self, metadata: dict) -> dict:
        """Garante que o metadata seja serializável e limpo."""
        return {
            k: v for k, v in metadata.items()
            if isinstance(v, (str, int, float, bool, list, dict))
        }

    def create_collection(self, collection_config: Dict[str, Any]):
        embeddings_model = collection_config['embeddings_model']
        local_embeddings = HuggingFaceEmbeddings(
            model_name=embeddings_model,
            model_kwargs={'trust_remote_code': True}
        )

        documents = collection_config['documents']
        chunk_size = collection_config['chunk_size']
        chunk_overlap = collection_config['chunk_overlap']

        if chunk_size == "Page":
            splits = documents
        else:
            if isinstance(chunk_size, str):
                raise ValueError("chunk_size deve ser 'Page' ou um inteiro.")
            if chunk_overlap is None:
                chunk_overlap = 0
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            splits = text_splitter.split_documents(documents)

        for doc in splits:
            doc.metadata = self.clean_metadata(doc.metadata)

        QdrantVectorStore.from_documents(
            documents=splits,
            embedding=local_embeddings,
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            collection_name=collection_config['collection_name'],
            force_recreate=True
        )

        print(f"Collection {collection_config['collection_name']} criada com sucesso.")

    def generate_collection_configs(self, documents_dict: Dict[str, List[Document]]) -> List[Dict[str, Any]]:
        embeddings_models = self.config['embeddings_models']
        chunk_sizes = self.config['chunk_sizes']
        chunk_overlaps = self.config['chunk_overlaps']

        all_docs = []
        for docs in documents_dict.values():
            all_docs.extend(docs)

        combos = itertools.product(embeddings_models, chunk_sizes, chunk_overlaps)
        configs = []
        for emb_model, c_size, c_overlap in combos:
            chunk_display = c_size if c_size != "Page" else "by-page"
            collection_name = (
                f"{self.config['collection_name']}_chunk{chunk_display}_overlap{c_overlap}_"
                f"{emb_model.split('/')[-1]}"
            )
            extraction_config = {
                "collection_name": collection_name,
                "chunk_size": c_size,
                "chunk_overlap": c_overlap,
                "embeddings_model": emb_model,
                "documents": all_docs,
            }
            configs.append(extraction_config)

        return configs

    def create_collections(self):
        documents_dict = {}
        for arquivo_id in self.config['arquivo_ids_to_process']:
            if not arquivo_id.startswith("fluidos_"):
                continue
            docs = self.load_json_documents(arquivo_id)
            if docs:
                documents_dict[arquivo_id] = docs

        self.collection_configs = self.generate_collection_configs(documents_dict)

        for collection_config in self.collection_configs:
            self.create_collection(collection_config)


if __name__ == "__main__":
    config_file = os.path.join(BASE_DIR, "config.json")
    processor = CollectionCreator(config_file)
    processor.create_collections()