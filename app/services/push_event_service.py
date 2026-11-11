import logging

from services.ai import push_analysis_graph


logger = logging.getLogger(__name__)


async def process_push_event_service(
    payload: dict,
    installation_id: int
):

    repository = payload.get("repository", {})

    repo_name = repository.get("full_name")

    if not repo_name:
        logger.warning("Repository name missing")
        return []

    commits = payload.get("commits", [])

    if not commits:
        logger.info("No commits found in push event")
        return []

    results = []

    for commit in commits:

        commit_sha = commit.get("id")

        if not commit_sha:
            continue

        initial_state = {

            "installation_id": installation_id,

            "repo_name": repo_name,

            "commit_sha": commit_sha,

            "push_event": payload
        }

        logger.info(
            "Starting AI analysis for repository=%s commit=%s",
            repo_name,
            commit_sha
        )

        result = await push_analysis_graph.ainvoke(
            initial_state
        )

        results.append({
            "commit_sha": commit_sha,
            "analysis": result.get("analysis")
        })

        logger.info(
            "AI analysis completed for commit=%s",
            commit_sha
        )

    return results