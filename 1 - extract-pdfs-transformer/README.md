# Extrator de PDFs

## Descrição
Este projeto tem como objetivo realizar a extração, processamento e análise de textos a partir de arquivos PDF. Utiliza modelos baseados em Transformers e modelos de Visão para tarefas como sumarização e perguntas e respostas (QA).

---

## Estrutura do Projeto

```plaintext
extract-pdfs-transformer/               # Módulo de extração
├── README.md                           # Documentação do projeto
├── requirements.txt                    # Dependências do projeto
├── data/
│   ├── raw/                                  # PDFs originais
│   ├── processed/                            # JSONs extraídos (pdf_parser)
│   ├── processed_clean/                      # JSONs após limpeza (process_clean)
│   ├── processed_pdf_to_images/              # PDFs convertidos em imagens (pdf_to_image)
│   ├── outputs_vision/                       # Resultados do Vision
│   ├── outputs_vision_and_extractor/         # Dados combinados extrator + Vision
│   ├── outputs_final_summaries/              # Sumários finais do documento
│   ├── references/                           # Referências para avaliação (sumários manuais)
│   └── logs/                                 # Logs
│
├── src/                                # Código-fonte principal
│   ├── __init__.py
│   ├── extract/                        # Módulo de extração
│   │   ├── pdf_parser.py               # Extração básica com PyMuPDF
│   │   └── transformer_vision.py       # Módulo de extração utilizando o Vision da Openai
│   │
│   ├── models/                         # Modelos de Transformers
│   │   ├── transformer_pipeline.py     # Outros modelos de transformers
│   │   └── evaluation.py               # Evaluation dos arquivos processados utilizando diferentes modelos.
│   │ 
│   ├── pipelines/ 
│   │   └── pipeline.py
│   │
│   ├── refine/ 
│   │   ├── process_clean.py            # Pré=processamento dos dados extraídos para remover ruídos              
│   │   └── data_refinement.py          # Unificação dos arquivos gerados dos extratores com o Vision
│   │
│   │── utils/                          # Funções utilitárias
│   │   ├── __init__.py
│   │   ├── file_utils.py               # Funções de criação de diretórios e manipulação de arquivos
│   │   ├── logging.py                  # Funções de apresentação de logs
│   │   └── pdf_to_image.py             # Módulo de tranformação de PDFs em imagens
│   │
│   └── vector_store/ 
│       ├── config.json
│       └── vectorstores.py 
│
└── notebooks/                          # Exploração inicial e validação
    ├── tests_extract.ipynb             # Testes do módulo de extração
    ├── tests_process_clean.ipynb       # Testes do pré=processamento dos dados extraídos para remover ruídos
    ├── tests_transformers.ipynb        # Testes de modelos diferentes de transformers
    ├── tests_transformer_vision.ipynb  # Testes do módulo de extração utilizando o Vision da Openai
    ├── tests_pdf_to_image.ipynb        # Testes do módulo de tranformação de PDFs em imagens
    └── tests_data_refinement.ipynb     # Testes de unificação dos arquivos gerados dos extratores com o Vision
