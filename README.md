# 🚀 GitHub Pull Request Fetcher & Cleanup Tool

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub API](https://img.shields.io/badge/API-GitHub%20REST-lightgrey.svg)](https://docs.github.com/en/rest)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/ishandutta2007/manage-github-pull-requests/graphs/commit-activity)
<a href="https://github.com/ishandutta2007"><img alt="GitHub followers" src="https://img.shields.io/github/followers/ishandutta2007?label=Follow" /></a>


An advanced, performance-optimized CLI utility designed for GitHub maintainers. It fetches, analyzes, and manages pull requests across hundreds of repositories with ease.

---

## ✨ Key Features

- **🔍 Deep PR Analysis**: Automatically detects merge conflicts in open pull requests by inspecting repository internals.
- **🛠️ Interactive Cleanup**: Close conflicted PRs directly from the terminal with standardized feedback comments. Supports individual confirmation or "Yes to All" ([y/N/a]).
- **⚡ Intelligent Caching**: 
  - **24-hour TTL**: Local JSON caching of repos, PR lists, and deep details.
  - **Auto-Sync**: Automatically invalidates local cache when you close a PR through the tool.
  - **Zero-PR Optimization**: Correctly caches repositories with no PRs to maximize speed.
- **⏱️ Progress & ETA Monitoring**: Real-time tracking of processing progress, elapsed time, and dynamic ETA calculation.
- **📄 Full Pagination**: Seamlessly handles accounts with massive repository counts and deep PR histories.
- **📂 Fork Filtering**: Automatically ignores forked repositories by default to focus on original content.

---

## 🛠️ Installation

### 1. Clone & Setup
```bash
git clone https://github.com/ishandutta2007/manage-github-pull-requests.git
cd manage-github-pull-requests
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
ADMIN_TOKEN=your_github_fine_grained_pat
```

#### 🔑 Required Token Permissions
To enable the **Interactive Cleanup** feature, your PAT needs **Read and Write** access for:
1. **Go to Settings**: [GitHub Fine-grained Tokens](https://github.com/settings/personal-access-tokens)
2. **Pull requests**: `Read and Write`
3. **Issues**: `Read and Write` (Required for posting closure comments)

---

## 🚀 Usage

The tool suite includes two specialized scripts for repository maintenance.

### 1. Merge Conflict Cleanup (`fetch_prs_and_close_conflicting.py`)
Scans all repositories and identifies open PRs that cannot be merged due to conflicts.

| Goal | Command |
| :--- | :--- |
| **Default Run** | `python fetch_prs_and_close_conflicting.py` |
| **Target Owner** | `python fetch_prs_and_close_conflicting.py <username>` |
| **Include Forks** | `python fetch_prs_and_close_conflicting.py --include-forks` |

### 2. User-Specific Cleanup (`fetch_prs_and_close_from_user.py`)
Scans repositories and identifies open PRs submitted by a specific user (e.g., to clean up bot spam or specific contributors).

| Goal | Command |
| :--- | :--- |
| **Standard Run** | `python fetch_prs_and_close_from_user.py --target-user <username>` |
| **Custom Owner** | `python fetch_prs_and_close_from_user.py --owner <org> --target-user <bot>` |

### Interactive Cleanup Modes
Both scripts support an interactive confirmation loop when blockers are identified:
- **`y`**: Close this PR with a standardized comment.
- **`N`**: Skip this PR (Default).
- **`a`**: **Yes to All**. Automatically close all remaining identified PRs in the session.

---

## 💾 Cache Management

The tool maintains a structured cache in the `.cache/` directory:
- `repos/`: List of user repositories.
- `prs/`: List of PRs per repository.
- `pr_details/`: Deep metadata for specific PRs (used for conflict detection).

**Note**: Closing a PR via the tool triggers an immediate `clear_cache()` for that repository, ensuring your next run reflects the updated state.

---

## 📂 Project Structure

```text
.
├── .cache/               # Multi-layer JSON cache
├── .env                  # Private GitHub token
├── fetch_prs_and_close_conflicting.py          # Advanced CLI Logic
├── fetch_prs_and_close_from_user.py            # Advanced CLI Logic
├── requirements.txt      # Dependencies
└── README.md             # Documentation
```

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

<a href="https://github.com/ishandutta2007"><img alt="GitHub followers" src="https://img.shields.io/github/followers/ishandutta2007?label=Follow" /></a>


---

## 📈 Star History

<div align="center">
  <a href="https://www.star-history.com/?repos=ishandutta2007%2Fmanage-github-pull-requests&type=date&legend=bottom-right">
   <picture>
     <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=ishandutta2007/manage-github-pull-requests&type=date&theme=dark&legend=bottom-right" />
     <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=ishandutta2007/manage-github-pull-requests&type=date&legend=bottom-right" />
     <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=ishandutta2007/manage-github-pull-requests&type=date&legend=bottom-right" />
   </picture>
  </a>
</div>

---

<p align="center">
  Made with ❤️ for efficient GitHub maintenance.<img alt="GitHub followers" src="https://img.shields.io/github/followers/ishandutta2007?label=Follow">
</p>
