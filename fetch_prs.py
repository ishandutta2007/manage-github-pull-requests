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

def get_paginated_data(url, params=None, cache_category=None, cache_id=None):
    if cache_category and cache_id and is_cache_valid(get_cache_path(cache_category, cache_id)):
        # print(f"    Using cached data for {cache_id}...")
        return load_from_cache(cache_category, cache_id)

    headers = get_headers()
    data = []
    current_url = url
    while current_url:
        response = requests.get(current_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching data from {current_url}: {response.status_code} - {response.text}")
            break
        
        data.extend(response.json())
        
        if 'next' in response.links:
            current_url = response.links['next']['url']
            params = None 
        else:
            current_url = None
    
    if cache_category and cache_id and data:
        save_to_cache(cache_category, cache_id, data)
        
    return data

def fetch_pull_requests(username):
    print(f"Fetching repositories for user: {username}...")
    repos_url = f"{API_URL}/users/{username}/repos"
    repos = get_paginated_data(repos_url, params={"per_page": 100, "type": "all"}, 
                               cache_category="repos", cache_id=username)
    
    if not repos:
        print(f"No repositories found for user {username} or error occurred.")
        return

    all_prs = []
    for repo in repos:
        repo_name = repo['name']
        owner = repo['owner']['login']
        full_name = f"{owner}/{repo_name}"
        
        # Check cache validity specifically to print the message
        cache_path = get_cache_path("prs", full_name)
        if is_cache_valid(cache_path):
            print(f"  Using cached pull requests for {full_name}")
        else:
            print(f"  Fetching pull requests for {full_name}...")
        
        prs_url = f"{API_URL}/repos/{full_name}/pulls"
        prs = get_paginated_data(prs_url, params={"state": "all", "per_page": 100},
                                 cache_category="prs", cache_id=full_name)
        
        for pr in prs:
            all_prs.append({
                "repo": full_name,
                "number": pr['number'],
                "title": pr['title'],
                "state": pr['state'],
                "url": pr['html_url'],
                "user": pr['user']['login']
            })
            
    return all_prs

def main():
    parser = argparse.ArgumentParser(description="Fetch all pull requests for all repos of a GitHub username.")
    parser.add_argument("username", nargs='?', help="GitHub username to fetch PRs for")
    parser.add_argument("--username", dest="username_flag", help="GitHub username to fetch PRs for (alternative to positional)")
    args = parser.parse_args()

    username = args.username_flag if args.username_flag else args.username
    
    if not username:
        username = "ishandutta2007"
        print(f"No username provided. Defaulting to: {username}")

    try:
        prs = fetch_pull_requests(username)
        
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
