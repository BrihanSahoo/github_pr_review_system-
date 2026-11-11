from typing import TypedDict, Any


class PushAnalysisState(TypedDict, total=False):

    installation_id: int

    repo_name: str

    commit_sha: str

    push_event: dict

    code_changes: dict

    context: str

    analysis: str

    error: str