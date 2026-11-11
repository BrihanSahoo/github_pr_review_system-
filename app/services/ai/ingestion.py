from langchain_core.documents import Document
from app.auth.vector_db_config import vector_store
from langchain_text_splitters import RecursiveCharacterTextSplitter


def index_repository_knowledge(
    repo_name:str,
    documents:list[str]
):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    docs = []
    for index,item in enumerate(documents):
        chunks = splitter.split_text(item['content'])
        
        for chunk,chunk_index in enumerate(chunks):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "repo": repo_name,
                        "source": "repository_knowledge",
                        "file_path": item.get("file_path", ""),
                        "document_id": str(index),
                        "chunk_id": str(chunk_index)
                    }
                )
            )
    if docs:
        vector_store.add_documents(docs)
    return len(docs)