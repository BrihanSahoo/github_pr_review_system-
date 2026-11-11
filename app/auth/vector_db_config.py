from langchain_chroma import Chroma
from app.auth.llm_config import embeddings

vector_store = Chroma(
    collection_name="github_knowledge",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)

retriever = vector_store.as_retriever(
    search_kwargs={"k": 4}
)