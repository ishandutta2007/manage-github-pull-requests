import sys
import requests
from .config import GITHUB_TOKEN, API_URL
from .cache import get_cache_path, is_cache_valid, load_from_cache, save_to_cache


def get_headers():
    if not GITHUB_TOKEN:
        print("Error: ADMIN_TOKEN not found in .env file.")
        sys.exit(1)
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_api_data(url, params=None, cache_category=None, cache_id=None):
    if cache_category and cache_id:
        cache_path = get_cache_path(cache_category, cache_id)
        if is_cache_valid(cache_path):
            return load_from_cache(cache_category, cache_id), True

    headers = get_headers()
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(
            f"Error fetching data from {url}: {response.status_code} - {response.text}"
        )
        return None, False

    data = response.json()

    # If it's a list, handle pagination
    if isinstance(data, list) and "next" in response.links:
        current_url = response.links["next"]["url"]
        while current_url:
            next_response = requests.get(current_url, headers=headers)
            if next_response.status_code != 200:
                break
            data.extend(next_response.json())
            current_url = (
                next_response.links["next"]["url"]
                if "next" in next_response.links
                else None
            )

    if cache_category and cache_id and data is not None:
        save_to_cache(cache_category, cache_id, data)

    return data, False


def get_authenticated_user():
    headers = get_headers()
    response = requests.get(f"{API_URL}/user", headers=headers)
    if response.status_code == 200:
        return response.json().get("login")
    return None


def fetch_pr_details(full_name, pr_number):
    cache_id = f"{full_name}_{pr_number}"
    url = f"{API_URL}/repos/{full_name}/pulls/{pr_number}"
    data, _ = get_api_data(url, cache_category="pr_details", cache_id=cache_id)
    return data


def close_pull_request(full_name, pr_number, comment):
    headers = get_headers()

    # 1. Add the comment
    comment_url = f"{API_URL}/repos/{full_name}/issues/{pr_number}/comments"
    comment_resp = requests.post(comment_url, headers=headers, json={"body": comment})
    if comment_resp.status_code != 201:
        print(
            f"      ❌ Failed to add comment: {comment_resp.status_code} - {comment_resp.text}"
        )
        return False

    # 2. Close the pull request
    close_url = f"{API_URL}/repos/{full_name}/pulls/{pr_number}"
    close_resp = requests.patch(close_url, headers=headers, json={"state": "closed"})
    if close_resp.status_code != 200:
        print(
            f"      ❌ Failed to close PR: {close_resp.status_code} - {close_resp.text}"
        )
        return False

    return True
