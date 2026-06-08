from .api import get_api_data, get_authenticated_user
from .config import API_URL


def get_repositories(owner_username, include_forks=False):
    auth_user = get_authenticated_user()

    if auth_user and auth_user.lower() == owner_username.lower():
        print(
            f"Fetching all repositories (public & private) for authenticated user: {owner_username}..."
        )
        repos_url = f"{API_URL}/user/repos"
        params = {"per_page": 100, "affiliation": "owner"}
    else:
        print(f"Fetching repositories for: {owner_username}...")
        repos_url = f"{API_URL}/orgs/{owner_username}/repos"
        params = {"per_page": 100}

        # Test if it's an org by doing a quick fetch, fallback to user
        from .api import get_headers
        import requests

        headers = get_headers()
        test_resp = requests.get(repos_url, headers=headers)
        if test_resp.status_code != 200:
            repos_url = f"{API_URL}/users/{owner_username}/repos"
            params = {"per_page": 100, "type": "all"}

    repos, repos_from_cache = get_api_data(
        repos_url, params=params, cache_category="repos", cache_id=owner_username
    )

    if repos_from_cache:
        print(f"✅ Retrieved repository list from cache.")
    else:
        print(f"🌐 Fetched repository list from API.")

    if not repos:
        print(f"No repositories found for user {owner_username} or error occurred.")
        return []

    filtered_repos = [r for r in repos if include_forks or r.get("fork") is not True]

    if not filtered_repos:
        print("No matching repositories to process.")

    return filtered_repos
