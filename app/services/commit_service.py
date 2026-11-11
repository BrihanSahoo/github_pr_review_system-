
import httpx

from auth.github_auth import create_installation_token
GITHUB_API = "https://api.github.com"



async def get_commit_changes_service(
    installation_id: int,
    repository_full_name: str,
    commit_sha: str,
) -> dict:

    """
    Fetch actual file changes for a GitHub commit.
    """

    token = await create_installation_token(
        str(installation_id)
    )

    owner, repo = repository_full_name.split("/", 1)

    url = (
        f"{GITHUB_API}/repos/{owner}/{repo}"
        f"/commits/{commit_sha}"
    )

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )

        response.raise_for_status()
        data = response.json()

    files = []

    for file in data.get("files", []):

        files.append({
            "filename": file.get("filename"),
            "status": file.get("status"),
            "additions": file.get("additions"),
            "deletions": file.get("deletions"),
            "changes": file.get("changes"),
            "patch": file.get("patch"),
            "blob_url": file.get("blob_url"),
            "raw_url": file.get("raw_url"),
        })

    return {
        "commit_sha": data.get("sha"),
        "commit_message": data.get("commit", {}).get(
            "message"
        ),
        "author": data.get("commit", {}).get(
            "author", {}
        ),
        "total_additions": data.get("stats", {}).get(
            "additions"
        ),
        "total_deletions": data.get("stats", {}).get(
            "deletions"
        ),
        "total_changes": data.get("stats", {}).get(
            "total"
        ),
        "files": files,
    }