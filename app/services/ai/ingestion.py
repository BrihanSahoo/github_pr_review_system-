from langchain_core.documents import Document
from auth.vector_db_config import vector_store


def index_repository_knowledge(
    repo_name:str,
    documents:list[str]
):
    docs = []
    for index,content in enumerate(documents):
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "repo": repo_name,
                    "source": "repository_knowledge",
                    "document_id": str(index),
                },
            )
        )
    vector_store.add_documents(docs)
    return len(docs)