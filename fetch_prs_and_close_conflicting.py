import argparse
import time
from datetime import timedelta
from github_tool import API_URL, get_repositories, get_api_data, fetch_pr_details, close_pull_request, clear_cache

def fetch_pull_requests(username, include_forks=False):
    repos = get_repositories(username, include_forks)
    total_repos = len(repos)
    
    if total_repos == 0:
        return [], []

    print(f"Processing {total_repos} repositories...")
    
    all_prs_data = []
    global_conflicted_prs = []
    start_time = time.time()
    
    for idx, repo in enumerate(repos, 1):
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


def main():
    parser = argparse.ArgumentParser(description="Fetch all pull requests for all repos of a GitHub username and close conflicting ones.")
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
