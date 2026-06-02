import os
import requests
from dotenv import load_dotenv
import argparse
import sys
import json
import time
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

GITHUB_TOKEN = os.getenv("ADMIN_TOKEN")
API_URL = "https://api.github.com"
CACHE_DIR = ".cache"
CACHE_EXPIRATION_HOURS = 24

def get_headers():
    if not GITHUB_TOKEN:
        print("Error: ADMIN_TOKEN not found in .env file.")
        sys.exit(1)
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_cache_path(category, identifier):
    # category: 'repos' or 'prs'
    # identifier: username or owner_repo
    clean_id = identifier.replace("/", "_")
    return os.path.join(CACHE_DIR, category, f"{clean_id}.json")

def is_cache_valid(cache_path):
    if not os.path.exists(cache_path):
        return False
    
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
            timestamp = cache_data.get("timestamp", 0)
            cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time < timedelta(hours=CACHE_EXPIRATION_HOURS):
                return True
    except (json.JSONDecodeError, KeyError):
        pass
    return False

def save_to_cache(category, identifier, data):
    cache_path = get_cache_path(category, identifier)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    cache_data = {
        "timestamp": time.time(),
        "data": data
    }
    with open(cache_path, 'w') as f:
        json.dump(cache_data, f, indent=2)

def load_from_cache(category, identifier):
    cache_path = get_cache_path(category, identifier)
    with open(cache_path, 'r') as f:
        return json.load(f)["data"]

def get_api_data(url, params=None, cache_category=None, cache_id=None):
    if cache_category and cache_id and is_cache_valid(get_cache_path(cache_category, cache_id)):
        return load_from_cache(cache_category, cache_id)

    headers = get_headers()
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error fetching data from {url}: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    
    # If it's a list, handle pagination
    if isinstance(data, list) and 'next' in response.links:
        current_url = response.links['next']['url']
        while current_url:
            next_response = requests.get(current_url, headers=headers)
            if next_response.status_code != 200:
                break
            data.extend(next_response.json())
            current_url = next_response.links['next']['url'] if 'next' in next_response.links else None

    if cache_category and cache_id and data:
        save_to_cache(cache_category, cache_id, data)
        
    return data

def fetch_pr_details(full_name, pr_number):
    cache_id = f"{full_name}_{pr_number}"
    url = f"{API_URL}/repos/{full_name}/pulls/{pr_number}"
    return get_api_data(url, cache_category="pr_details", cache_id=cache_id)

def fetch_pull_requests(username, include_forks=False):
    print(f"Fetching repositories for user: {username}...")
    repos_url = f"{API_URL}/users/{username}/repos"
    repos = get_api_data(repos_url, params={"per_page": 100, "type": "all"}, 
                               cache_category="repos", cache_id=username)
    
    if not repos:
        print(f"No repositories found for user {username} or error occurred.")
        return

    # Pre-filter repos to get an accurate count for progress tracking
    filtered_repos = [r for r in repos if include_forks or r.get('fork') is not True]
    total_repos = len(filtered_repos)
    
    if total_repos == 0:
        print("No matching repositories to process.")
        return

    print(f"Processing {total_repos} repositories...")
    
    all_prs_data = []
    start_time = time.time()
    
    for idx, repo in enumerate(filtered_repos, 1):
        repo_name = repo['name']
        owner = repo['owner']['login']
        full_name = f"{owner}/{repo_name}"
        
        # Calculate timing and ETA
        elapsed = time.time() - start_time
        avg_time_per_repo = elapsed / (idx - 1) if idx > 1 else 0
        remaining_repos = total_repos - (idx - 1)
        eta_seconds = avg_time_per_repo * remaining_repos
        
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        eta_str = str(timedelta(seconds=int(eta_seconds))) if idx > 1 else "--:--:--"
        
        progress_header = f"[{idx}/{total_repos}] | Elapsed: {elapsed_str} | ETA: {eta_str}"
        
        cache_path = get_cache_path("prs", full_name)
        is_from_cache = is_cache_valid(cache_path)
        
        status = "(Cached)" if is_from_cache else "(Fetching...)"
        print(f"\n{progress_header} \n📦 {full_name} {status}")
        
        prs_url = f"{API_URL}/repos/{full_name}/pulls"
        prs = get_api_data(prs_url, params={"state": "all", "per_page": 100},
                                 cache_category="prs", cache_id=full_name)
        
        if not prs:
            print("   No pull requests found.")
            continue

        open_prs = [p for p in prs if p['state'] == 'open']
        closed_prs = [p for p in prs if p['state'] == 'closed']
        
        conflict_count = 0
        if open_prs:
            print(f"   Checking {len(open_prs)} open PRs for conflicts...")
            for pr in open_prs:
                pr_detail = fetch_pr_details(full_name, pr['number'])
                # 'mergeable' can be True, False, or None (if GitHub is still calculating)
                if isinstance(pr_detail, dict) and pr_detail.get('mergeable') is False:
                    conflict_count += 1
        
        print(f"   📊 Stats: Total: {len(prs)} | 🟢 Open: {len(open_prs)} | 🔴 Closed: {len(closed_prs)} | ⚠️ Conflicts: {conflict_count}")
        
        for pr in prs:
            all_prs_data.append({
                "repo": full_name,
                "number": pr['number'],
                "title": pr['title'],
                "state": pr['state'],
                "url": pr['html_url'],
                "user": pr['user']['login'],
                "has_conflict": (pr['state'] == 'open' and conflict_count > 0)
            })
            
    return all_prs_data

def main():
    parser = argparse.ArgumentParser(description="Fetch all pull requests for all repos of a GitHub username.")
    parser.add_argument("username", nargs='?', help="GitHub username to fetch PRs for")
    parser.add_argument("--username", dest="username_flag", help="GitHub username to fetch PRs for (alternative to positional)")
    parser.add_argument("--include-forks", action="store_true", help="Include forked repositories (default: False)")
    args = parser.parse_args()

    username = args.username_flag if args.username_flag else args.username
    
    if not username:
        username = "ishandutta2007"
        print(f"No username provided. Defaulting to: {username}")

    try:
        prs = fetch_pull_requests(username, include_forks=args.include_forks)
        
        if prs:
            print(f"\nFound {len(prs)} pull requests:")
            print("-" * 80)
            for pr in prs:
                print(f"[{pr['repo']}] #{pr['number']} {pr['title']} ({pr['state']})")
                print(f"   URL: {pr['url']}")
                print(f"   Author: {pr['user']}")
                print("-" * 80)
        else:
            print("No pull requests found.")
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
