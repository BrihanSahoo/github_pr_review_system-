from auth.vector_db_config import retriever

async def retrieve_context(
    repo_name : str,
    query : str
):
    docs = await retriever.ainvoke(query)
    relevant_docs = [
        doc
        for doc in docs
        if doc.metadata.get("repo") == repo_name
    ]
    context = "\n\n".join(
        doc.page_content
        for doc in relevant_docs
    )
    return context