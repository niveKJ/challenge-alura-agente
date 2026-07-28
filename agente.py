"""
Agente Alura Agente - BimBam Buy
---------------------------------
Agente de IA que responde preguntas en lenguaje natural sobre la Política de
Reembolsos y Devoluciones de BimBam Buy, usando LangChain + Cohere.

Arquitectura (RAG - Retrieval Augmented Generation):
1. Carga del PDF con PyPDFLoader (pypdf).
2. División del texto en fragmentos (chunks) con RecursiveCharacterTextSplitter.
3. Generación de embeddings con Cohere (embed-multilingual-v3.0) y
   almacenamiento en un índice vectorial FAISS (en memoria).
4. Recuperación de los fragmentos más relevantes para la pregunta del usuario.
5. Generación de la respuesta final con el modelo de chat de Cohere
   (command-r-plus), usando los fragmentos recuperados como contexto.
"""

import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain.chains import RetrievalQA

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PDF_PATH = os.getenv("PDF_PATH", "data/politica_reembolsos_bimbam_buy.pdf")

if not COHERE_API_KEY:
    raise RuntimeError(
        "Falta la variable de entorno COHERE_API_KEY. "
        "Copia .env.example a .env y coloca tu API key de Cohere."
    )


def build_agent(pdf_path: str = PDF_PATH):
    """Construye el pipeline RAG y devuelve una cadena de preguntas y respuestas."""

    # 1. Cargar el documento
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # 2. Dividir en fragmentos manejables
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(documents)

    # 3. Crear embeddings y el índice vectorial
    embeddings = CohereEmbeddings(
        cohere_api_key=COHERE_API_KEY,
        model="embed-multilingual-v3.0",
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 4. Configurar el modelo de lenguaje (LLM)
    llm = ChatCohere(
        cohere_api_key=COHERE_API_KEY,
        model="command-r-plus",
        temperature=0,
    )

    # 5. Cadena de RetrievalQA (recupera contexto + genera respuesta)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True,
    )
    return qa_chain


def ask(qa_chain, question: str) -> str:
    """Envía una pregunta al agente y devuelve la respuesta en texto plano."""
    result = qa_chain.invoke({"query": question})
    return result["result"]


def main():
    print("=" * 60)
    print("Agente BimBam Buy - Política de Reembolsos y Devoluciones")
    print("Escribe tu pregunta o 'salir' para terminar.")
    print("=" * 60)

    qa_chain = build_agent()

    while True:
        question = input("\nTu pregunta: ").strip()
        if question.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break
        if not question:
            continue

        respuesta = ask(qa_chain, question)
        print(f"\nRespuesta: {respuesta}")


if __name__ == "__main__":
    main()
