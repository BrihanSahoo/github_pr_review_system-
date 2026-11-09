
import logging

import httpx

from app.services.commit_service import get_commit_changes_service


GITHUB_API = "https://api.github.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

async def process_push_event_service(
    payload: dict,
    installation_id: int,
):

    repository = payload.get("repository") or {}
    sender = payload.get("sender") or {}

    repo_name = repository.get("full_name")
    branch = payload.get("ref")
    username = sender.get("login")

    commits = payload.get("commits", [])

    logger.info("========== GITHUB PUSH EVENT ==========")
    logger.info("Repository: %s", repo_name)
    logger.info("Branch: %s", branch)
    logger.info("Pushed by: %s", username)
    logger.info("Total commits: %s", len(commits))

    for commit in commits:

        commit_sha = commit.get("id")

        logger.info("-----------------------------------")
        logger.info("Fetching commit: %s", commit_sha)

        try:
            changes = await get_commit_changes_service(
                installation_id=installation_id,
                repository_full_name=repo_name,
                commit_sha=commit_sha,
            )

            logger.info(
                "Commit message: %s",
                changes["commit_message"],
            )

            logger.info(
                "Total additions: %s",
                changes["total_additions"],
            )

            logger.info(
                "Total deletions: %s",
                changes["total_deletions"],
            )

            for file in changes["files"]:

                logger.info(
                    "FILE: %s | STATUS: %s | +%s | -%s",
                    file["filename"],
                    file["status"],
                    file["additions"],
                    file["deletions"],
                )

                patch = file.get("patch")

                if patch:
                    logger.info(
                        "ACTUAL CODE CHANGES:\n%s",
                        patch,
                    )
                else:
                    logger.info(
                        "Patch unavailable for: %s",
                        file["filename"],
                    )

        except httpx.HTTPStatusError as exc:
            logger.exception(
                "GitHub API error for commit %s: %s",
                commit_sha,
                exc.response.text,
            )

        except Exception:
            logger.exception(
                "Failed to process commit: %s",
                commit_sha,
            )

    logger.info("========== END PUSH EVENT ==========")