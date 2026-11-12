import json

from app.services.github.commit_service import get_commit_changes_service
from app.services.ai.graph_state import PushAnalysisState
from app.services.ai.retrieval import retrieve_context
from app.services.ai.prompts import push_analysis_prompt
from app.auth.llm_config import llm




async def fetch_changes_node(
    state : PushAnalysisState
):
    changes = await get_commit_changes_service(
        installation_id=state["installation_id"],
        repository_full_name=state["repo_name"],
        commit_sha=state["commit_sha"]
    )
    return {
        "code_changes": changes
    }
    
    
async def retrieve_context_node(
    state : PushAnalysisState
):
    changes = state["code_changes"]
    filenames = [
        file["filename"]
        for file in changes.get("files", [])
    ]
    
    query = f"""
    Repository: {state['repo_name']}

    Commit message:
    {changes.get('commit_message')}

    Modified files:
    {', '.join(filenames)}

    Understand the architecture, dependencies,
    implementation and functionality related
    to these changed files.
    """
    
    context = retrieve_context(
        repo_name=state['repo_name'],
        query=query
    )
    return {
        "context": context
    }
    
    

async def analyze_changes_node(
    state: PushAnalysisState
):

    chain = push_analysis_prompt | llm

    result = await chain.ainvoke({

        "repo_name": state["repo_name"],

        "push_event": json.dumps(
            state["push_event"],
            indent=2
        ),

        "code_changes": json.dumps(
            state["code_changes"],
            indent=2
        ),

        "context": state["context"]
    })

    return {
        "analysis": result.content
    }