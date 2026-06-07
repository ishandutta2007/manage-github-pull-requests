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

def clear_cache(category, identifier):
    cache_path = get_cache_path(category, identifier)
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except OSError:
            pass

def get_api_data(url, params=None, cache_category=None, cache_id=None):
    if cache_category and cache_id:
        cache_path = get_cache_path(cache_category, cache_id)
        # print(f"DEBUG: Checking cache for {cache_id} at {cache_path}")
        if is_cache_valid(cache_path):
            return load_from_cache(cache_category, cache_id), True
        # else:
        #    print(f"DEBUG: Cache invalid for {cache_path}")

    headers = get_headers()
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error fetching data from {url}: {response.status_code} - {response.text}")
        return None, False
    
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

    if cache_category and cache_id and data is not None:
        save_to_cache(cache_category, cache_id, data)
        
    return data, False

def fetch_pr_details(full_name, pr_number):
    cache_id = f"{full_name}_{pr_number}"
    url = f"{API_URL}/repos/{full_name}/pulls/{pr_number}"
    data, _ = get_api_data(url, cache_category="pr_details", cache_id=cache_id)
    return data

def fetch_pull_requests(username, include_forks=False):
    print(f"Fetching repositories for user: {username}...")
    repos_url = f"{API_URL}/users/{username}/repos"
    repos, repos_from_cache = get_api_data(repos_url, params={"per_page": 100, "type": "all"}, 
                               cache_category="repos", cache_id=username)
    
    if repos_from_cache:
        print(f"✅ Retrieved repository list from cache.")
    else:
        print(f"🌐 Fetched repository list from API.")

    if not repos:
        print(f"No repositories found for user {username} or error occurred.")
        return [], []

    # Pre-filter repos to get an accurate count for progress tracking
    filtered_repos = [r for r in repos if include_forks or r.get('fork') is not True]
    total_repos = len(filtered_repos)
    
    if total_repos == 0:
        print("No matching repositories to process.")
        return [], []

    print(f"Processing {total_repos} repositories...")
    
    all_prs_data = []
    global_conflicted_prs = []
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
        
        prs_url = f"{API_URL}/repos/{full_name}/pulls"
        prs, is_from_cache = get_api_data(prs_url, params={"state": "all", "per_page": 100},
                                 cache_category="prs", cache_id=full_name)
        
        status = "(Retrieving from cache...)" if is_from_cache else "(Fetching from API...)"
        print(f"\n{progress_header} \n📦 {full_name} {status}")
        
        if not prs:
            print("   No pull requests found.")
            continue

        open_prs = [p for p in prs if p['state'] == 'open']
        closed_prs = [p for p in prs if p['state'] == 'closed']
        
        repo_conflicts = []
        if open_prs:
            print(f"   Checking {len(open_prs)} open PRs for conflicts...")
            for pr in open_prs:
                pr_detail = fetch_pr_details(full_name, pr['number'])
                # 'mergeable' can be True, False, or None (if GitHub is still calculating)
                if isinstance(pr_detail, dict) and pr_detail.get('mergeable') is False:
                    conflict_info = {
                        "repo": full_name,
                        "number": pr['number'],
                        "title": pr['title'],
                        "user": pr['user']['login'],
                        "url": pr['html_url']
                    }
                    repo_conflicts.append(conflict_info)
                    global_conflicted_prs.append(conflict_info)
        
        print(f"   📊 Stats: Total: {len(prs)} | 🟢 Open: {len(open_prs)} | 🔴 Closed: {len(closed_prs)} | ⚠️ Conflicts: {len(repo_conflicts)}")
        
        if open_prs:
            print("\n      " + "-" * 110)
            print(f"      {'#':<5} | {'Title':<50} | {'Author':<20} | {'Conflict'}")
            print("      " + "-" * 110)
            for pr in open_prs:
                # Find if this PR is in the repo_conflicts list we just built
                is_conflicted = any(c['number'] == pr['number'] for c in repo_conflicts)
                conflict_status = "⚠️ YES" if is_conflicted else "✅ NO"
                title_truncated = (pr['title'][:47] + '..') if len(pr['title']) > 50 else pr['title']
                print(f"      {pr['number']:<5} | {title_truncated:<50} | {pr['user']['login']:<20} | {conflict_status}")
            print("      " + "-" * 110 + "\n")

        for pr in prs:
            all_prs_data.append({
                "repo": full_name,
                "number": pr['number'],
                "title": pr['title'],
                "state": pr['state'],
                "url": pr['html_url'],
                "user": pr['user']['login']
            })
            
    return all_prs_data, global_conflicted_prs

def close_pull_request(full_name, pr_number, comment):
    headers = get_headers()
    
    # 1. Add the "merge conflict" comment
    comment_url = f"{API_URL}/repos/{full_name}/issues/{pr_number}/comments"
    comment_resp = requests.post(comment_url, headers=headers, json={"body": comment})
    if comment_resp.status_code != 201:
        print(f"      ❌ Failed to add comment: {comment_resp.status_code} - {comment_resp.text}")
        return False

    # 2. Close the pull request
    close_url = f"{API_URL}/repos/{full_name}/pulls/{pr_number}"
    close_resp = requests.patch(close_url, headers=headers, json={"state": "closed"})
    if close_resp.status_code != 200:
        print(f"      ❌ Failed to close PR: {close_resp.status_code} - {close_resp.text}")
        return False
    
    return True

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
        all_prs, conflicted_prs = fetch_pull_requests(username, include_forks=args.include_forks)
        
        if conflicted_prs:
            print("\n" + "=" * 125)
            print("🚨 FINAL SUMMARY: OPEN PULL REQUESTS WITH MERGE CONFLICTS")
            print("=" * 125)
            print(f"{'Repository':<40} | {'#':<5} | {'Title':<50} | {'Author'}")
            print("-" * 125)
            for pr in conflicted_prs:
                title_truncated = (pr['title'][:47] + '..') if len(pr['title']) > 50 else pr['title']
                print(f"{pr['repo']:<40} | {pr['number']:<5} | {title_truncated:<50} | {pr['user']}")
            print("-" * 125)
            print(f"Total Blocker PRs: {len(conflicted_prs)}")
            print("=" * 125 + "\n")

            # INTERACTIVE SECTION
            print("🛠️  Interactive Cleanup: Would you like to close these conflicted PRs?")
            print("Options: [y]es, [N]o (default), [a]ll (yes to all remaining)")
            
            yes_to_all = False
            for pr in conflicted_prs:
                print(f"\n      PR: {pr['title']}")
                print(f"      URL: {pr['url']}")
                
                if yes_to_all:
                    choice = 'y'
                else:
                    prompt = f"      Close [{pr['repo']}] #{pr['number']}? (y/N/a): "
                    choice = input(prompt).strip().lower()
                    if choice == 'a':
                        yes_to_all = True
                        choice = 'y'
                
                if choice == 'y':
                    comment_text = "this change has merge conflicts, please make changes on the latest main branch and send us a PR again"
                    print(f"   🚀 Processing #{pr['number']}...")
                    if close_pull_request(pr['repo'], pr['number'], comment_text):
                        print(f"   ✅ Successfully commented and closed.")
                        # Clear cache so next run reflects the change
                        clear_cache("prs", pr['repo'])
                        clear_cache("pr_details", f"{pr['repo']}_{pr['number']}")
                    else:
                        print(f"   ⚠️  Manual intervention required for #{pr['number']}.")
                else:
                    print(f"   ⏩ Skipping #{pr['number']}.")
            print("\n" + "=" * 125 + "\n")
        else:
            print("\n" + "=" * 125)
            print("🎉 FINAL SUMMARY: NO MERGE CONFLICTS FOUND")
            print("=" * 125 + "\n")

        if all_prs:
            print(f"Completed! Processed a total of {len(all_prs)} pull requests.")
        else:
            print("No pull requests found.")
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
