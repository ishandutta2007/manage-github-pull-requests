import os
import requests
from dotenv import load_dotenv
import argparse
import sys

# Load environment variables from .env file
load_dotenv()

GITHUB_TOKEN = os.getenv("ADMIN_TOKEN")
API_URL = "https://api.github.com"

def get_headers():
    if not GITHUB_TOKEN:
        print("Error: ADMIN_TOKEN not found in .env file.")
        sys.exit(1)
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_paginated_data(url, params=None):
    headers = get_headers()
    data = []
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching data from {url}: {response.status_code} - {response.text}")
            break
        
        data.extend(response.json())
        
        # Check for next page in Link header
        if 'next' in response.links:
            url = response.links['next']['url']
            params = None # Params are already in the next URL
        else:
            url = None
    return data

def fetch_pull_requests(username):
    print(f"Fetching repositories for user: {username}...")
    repos_url = f"{API_URL}/users/{username}/repos"
    repos = get_paginated_data(repos_url, params={"per_page": 100, "type": "all"})
    
    if not repos:
        print(f"No repositories found for user {username} or error occurred.")
        return

    all_prs = []
    for repo in repos:
        repo_name = repo['name']
        owner = repo['owner']['login']
        print(f"  Fetching pull requests for {owner}/{repo_name}...")
        
        prs_url = f"{API_URL}/repos/{owner}/{repo_name}/pulls"
        prs = get_paginated_data(prs_url, params={"state": "all", "per_page": 100})
        
        for pr in prs:
            all_prs.append({
                "repo": f"{owner}/{repo_name}",
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
