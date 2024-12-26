import os
import streamlit as st
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_qdrant import QdrantVectorStore
from ragas.evaluation import evaluate, EvaluationDataset
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
from ragas.llms.base import LangchainLLMWrapper

# Carrega variáveis de ambiente do .env
load_dotenv()

# Função para validar variáveis de ambiente
def validate_env_vars():
    required_vars = ["QDRANT_URL", "QDRANT_API_KEY", "OPENAI_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            st.error(f"Variável de ambiente {var} não definida. Verifique o arquivo .env.")
            raise EnvironmentError(f"Missing required environment variable: {var}")

validate_env_vars()

# Carregando variáveis de ambiente
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Função para formatar documentos recuperados
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs if doc.page_content)

# Função para inicializar embeddings e modelo
def initialize_embeddings_and_model():
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'trust_remote_code': True}
        )
        model = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=OPENAI_API_KEY
        )
        return embeddings, model
    except Exception as e:
        st.error("Erro ao inicializar embeddings ou modelo.")
        st.exception(e)
        raise

# Função para carregar o vetorstore
def load_vectorstore(embeddings):
    try:
        vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=embeddings,
            collection_name="fluidos_chunkby-page_overlap0_multilingual-e5-large",
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )
        return vectorstore
    except Exception as e:
        st.error("Erro ao conectar ou carregar a coleção Qdrant.")
        st.exception(e)
        raise

# Função para calcular métricas RAGAS
def calculate_ragas_metrics(question, answer, docs, reference, llm):
    try:
        evaluation_dataset = EvaluationDataset.from_list([{
            "user_input": question,
            "response": answer,
            "retrieved_contexts": [doc.page_content for doc in docs],
            "reference": reference
        }])

        metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()]

        evaluation_result = evaluate(
            evaluation_dataset,
            metrics=metrics,
            llm=llm
        )

        return evaluation_result.scores[0]
    except Exception as e:
        st.error("Erro durante o cálculo das métricas RAGAS.")
        st.exception(e)
        return None

# Função principal
def main():
    st.title("Vehicle Manuals QA with RAGAS Evaluation")

    # Inputs do usuário
    question = st.text_input("Digite sua pergunta:")
    reference_answer = st.text_input("Digite a resposta de referência esperada:")
    arquivo_id = st.text_input("Digite o 'arquivo_id' desejado (opcional):")

    if not question:
        st.write("Por favor, insira uma pergunta acima.")
        return

    if not reference_answer:
        st.write("Por favor, insira a resposta de referência acima.")
        return

    st.write("Inicializando embeddings e modelo...")
    embeddings, model = initialize_embeddings_and_model()

    st.write("Carregando coleção existente do Qdrant...")
    vectorstore = load_vectorstore(embeddings)

    # Aplicar filtro com base no arquivo_id
    filter_condition = None
    if arquivo_id:
        try:
            arquivo_id = int(arquivo_id)  # Garante que seja inteiro
            filter_condition = {
                "must": [
                    {"key": "metadata.arquivo_id", "match": {"value": arquivo_id}}
                ]
            }
            st.write(f"Filtrando resultados para 'arquivo_id': {arquivo_id}")
        except ValueError:
            st.error("O 'arquivo_id' deve ser um número inteiro.")
            return

    retriever = vectorstore.as_retriever(search_kwargs={"filter": filter_condition})

    RAG_TEMPLATE = """
    Você é um assistente para tarefas de perguntas e respostas. Use os seguintes trechos de contexto recuperado para responder à pergunta.
    Se você não souber a resposta, simplesmente diga que não sabe.
    <context>{context}</context> Responda à seguinte pergunta: {question}
    """

    rag_prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)

    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        | rag_prompt
        | model
        | RunnableLambda(lambda x: x.content if hasattr(x, 'content') else x)
    )

    rag_chain_with_source = (
        RunnableParallel(
            {
                "context": RunnableLambda(lambda q: retriever.invoke(q)),
                "question": RunnablePassthrough()
            }
        ).assign(answer=rag_chain_from_docs)
    )

    st.write("Invocando a cadeia RAG...")
    try:
        result = rag_chain_with_source.invoke(question)
        st.write("Cadeia RAG executada com sucesso.")
    except Exception as e:
        st.error("Erro ao invocar a cadeia RAG.")
        st.exception(e)
        return

    # Exibição da pergunta e resposta
    st.subheader("Pergunta:")
    st.write(result.get('question', '').strip())

    st.subheader("Resposta:")
    st.write(result.get('answer', 'Sem resposta disponível').strip())

    # Exibição dos documentos recuperados
    st.subheader("Documentos Recuperados:")
    docs = result.get('context', [])
    st.write(f"Foram recuperados {len(docs)} documentos.")
    for i, doc in enumerate(docs, 1):
        st.markdown(f"**Documento {i}:**")
        st.markdown(f"**Fonte:** {doc.metadata.get('source', '').strip()}")
        st.markdown(f"**Conteúdo:** {doc.page_content[:500].strip()}...")

    # Avaliação RAGAS
    st.write("Calculando métricas RAGAS...")
    llm_for_ragas = LangchainLLMWrapper(model)
    ragas_scores = calculate_ragas_metrics(
        question=result.get('question', ''),
        answer=result.get('answer', ''),
        docs=docs,
        reference=reference_answer,
        llm=llm_for_ragas
    )

    if ragas_scores:
        st.subheader("Métricas de Avaliação RAGAS:")
        st.write(f"**Fidelidade:** {ragas_scores['faithfulness']:.2f}")
        st.write(f"**Relevância da Resposta:** {ragas_scores['answer_relevancy']:.2f}")
        st.write(f"**Precisão do Contexto:** {ragas_scores['context_precision']:.2f}")
        st.write(f"**Revocação do Contexto:** {ragas_scores['context_recall']:.2f}")
    else:
        st.error("Não foi possível calcular as métricas RAGAS.")

if __name__ == "__main__":
    main()