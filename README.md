<h1 align="center">Doutor IE RAG experiments</h1>

<p align="center">
  Experiments for the implementation of a RAG that help in the search for pertinent information from the automotive world. Being powered by high quality manuals provided by Doutor IE.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
  <img src="https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white" />
  <img src="https://img.shields.io/badge/cuda-000000.svg?style=for-the-badge&logo=nVIDIA&logoColor=green" />
</p>


## How to run:

In the src directory you will be able to see different apps with different purposes. Among them, the main one is `st-app.py` and `retrievel.py`, which presents a Streamlit application for the current version of RAG. Run the following command to run this application:

```bash
source venv/bin/activate

streamlit run src/st-app.py

OR

streamlit run src/retrievel.py
```

## Necessary services:

The RAG uses **Llama 3.1 8b** as its main model. This must be running locally with ollama. In addition, it is also necessary to have an instance of **Qdrant** also running locally on port `6333`
