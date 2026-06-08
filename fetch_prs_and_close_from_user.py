import argparse
import time
from datetime import timedelta
from github_tool import (
    API_URL,
    get_repositories,
    get_api_data,
    fetch_pr_details,
    close_pull_request,
    clear_cache,
)


def fetch_pull_requests(owner_username, target_user_login, include_forks=False):
    repos = get_repositories(owner_username, include_forks)
    total_repos = len(repos)

    if total_repos == 0:
        return [], []

    print(
        f"Processing {total_repos} repositories, looking for PRs from: {target_user_login}"
    )

    all_prs_data = []
    target_user_prs = []
    start_time = time.time()

    for idx, repo in enumerate(repos, 1):
        repo_name = repo["name"]
        owner = repo["owner"]["login"]
        full_name = f"{owner}/{repo_name}"

        # Calculate timing and ETA
        elapsed = time.time() - start_time
        avg_time_per_repo = elapsed / (idx - 1) if idx > 1 else 0
        remaining_repos = total_repos - (idx - 1)
        eta_seconds = avg_time_per_repo * remaining_repos

        elapsed_str = str(timedelta(seconds=int(elapsed)))
        eta_str = str(timedelta(seconds=int(eta_seconds))) if idx > 1 else "--:--:--"

        progress_header = (
            f"[{idx}/{total_repos}] | Elapsed: {elapsed_str} | ETA: {eta_str}"
        )

        prs_url = f"{API_URL}/repos/{full_name}/pulls"
        prs, is_from_cache = get_api_data(
            prs_url,
            params={"state": "open", "per_page": 100},
            cache_category="prs",
            cache_id=full_name,
        )

        status = (
            "(Retrieving from cache...)" if is_from_cache else "(Fetching from API...)"
        )
        print(f"\n{progress_header} \n📦 {full_name} {status}")

        if not prs:
            print("   No open pull requests found.")
            continue

        repo_target_prs = [
            p for p in prs if p["user"]["login"].lower() == target_user_login.lower()
        ]

        print(
            f"   📊 Stats: Total Open: {len(prs)} | 🎯 From {target_user_login}: {len(repo_target_prs)}"
        )

        if repo_target_prs:
            print("\n      " + "-" * 110)
            print(f"      {'#':<5} | {'Title':<50} | {'Author':<20}")
            print("      " + "-" * 110)
            for pr in repo_target_prs:
                title_truncated = (
                    (pr["title"][:47] + "..") if len(pr["title"]) > 50 else pr["title"]
                )
                print(
                    f"      {pr['number']:<5} | {title_truncated:<50} | {pr['user']['login']:<20}"
                )

                target_user_prs.append(
                    {
                        "repo": full_name,
                        "number": pr["number"],
                        "title": pr["title"],
                        "user": pr["user"]["login"],
                        "url": pr["html_url"],
                    }
                )
            print("      " + "-" * 110 + "\n")

        for pr in prs:
            all_prs_data.append(
                {
                    "repo": full_name,
                    "number": pr["number"],
                    "title": pr["title"],
                    "user": pr["user"]["login"],
                }
            )

    return all_prs_data, target_user_prs


def main():
    parser = argparse.ArgumentParser(
        description="Fetch all pull requests and close ones from a specific user."
    )
    parser.add_argument(
        "--owner",
        default="ishandutta2007",
        help="GitHub username whose repos to scan (default: ishandutta2007)",
    )
    parser.add_argument(
        "--target-user",
        required=True,
        help="GitHub username whose PRs you want to close",
    )
    parser.add_argument(
        "--include-forks", action="store_true", help="Include forked repositories"
    )
    args = parser.parse_args()

    try:
        all_prs, target_prs = fetch_pull_requests(
            args.owner, args.target_user, include_forks=args.include_forks
        )

        if target_prs:
            print("\n" + "=" * 125)
            print(f"🚨 FINAL SUMMARY: OPEN PULL REQUESTS FROM {args.target_user}")
            print("=" * 125)
            print(f"{'Repository':<40} | {'#':<5} | {'Title':<50} | {'Author'}")
            print("-" * 125)
            for pr in target_prs:
                title_truncated = (
                    (pr["title"][:47] + "..") if len(pr["title"]) > 50 else pr["title"]
                )
                print(
                    f"{pr['repo']:<40} | {pr['number']:<5} | {title_truncated:<50} | {pr['user']}"
                )
            print("-" * 125)
            print(f"Total Target PRs: {len(target_prs)}")
            print("=" * 125 + "\n")

            # INTERACTIVE SECTION
            print(
                f"🛠️  Interactive Cleanup: Would you like to close these PRs from {args.target_user}?"
            )
            print("Options: [y]es, [N]o (default), [a]ll (yes to all remaining)")

            yes_to_all = False
            for pr in target_prs:
                print(f"\n      PR: {pr['title']}")
                print(f"      URL: {pr['url']}")

                if yes_to_all:
                    choice = "y"
                else:
                    prompt = f"      Close [{pr['repo']}] #{pr['number']}? (y/N/a): "
                    choice = input(prompt).strip().lower()
                    if choice == "a":
                        yes_to_all = True
                        choice = "y"

                if choice == "y":
                    comment_text = f"Closing pull request from {args.target_user} as part of automated cleanup."
                    print(f"   🚀 Processing #{pr['number']}...")
                    if close_pull_request(pr["repo"], pr["number"], comment_text):
                        print(f"   ✅ Successfully commented and closed.")
                        clear_cache("prs", pr["repo"])
                    else:
                        print(
                            f"   ⚠️  Manual intervention required for #{pr['number']}."
                        )
                else:
                    print(f"   ⏩ Skipping #{pr['number']}.")
            print("\n" + "=" * 125 + "\n")
        else:
            print("\n" + "=" * 125)
            print(f"🎉 FINAL SUMMARY: NO OPEN PRS FOUND FROM {args.target_user}")
            print("=" * 125 + "\n")

        print(
            f"Completed! Processed a total of {len(all_prs)} open pull requests across all scanned repos."
        )

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
