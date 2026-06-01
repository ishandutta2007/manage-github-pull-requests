# 🚀 GitHub Pull Request Fetcher

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub API](https://img.shields.io/badge/API-GitHub%20REST-lightgrey.svg)](https://docs.github.com/en/rest)

A powerful, efficient CLI tool designed to fetch all pull requests across all repositories for any GitHub user. Built with performance in mind, it features intelligent local caching and seamless API integration.

---

## ✨ Features

- **🔍 Comprehensive Search**: Fetches PRs from every repository owned by a user.
- **⚡ Intelligent Caching**: Local disk caching with a 24-hour TTL to save API rate limits and improve speed.
- **📄 Pagination Support**: Automatically handles GitHub API pagination for users with hundreds of repos or PRs.
- **🛠️ Flexible CLI**: Use positional arguments or flags, with a sensible default for quick lookups.
- **🔒 Secure**: Uses `.env` files to protect your sensitive GitHub Personal Access Tokens.

---

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/manage-github-pull-requests.git
cd manage-github-pull-requests
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory and add your GitHub Admin Token:
```env
ADMIN_TOKEN=your_github_pat_here
```
> **Note**: Ensure your token has `repo` and `read:org` permissions to access private data if required.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

The tool is designed to be simple and intuitive.

### Default Usage
Fetch PRs for the default user (`ishandutta2007`):
```bash
python fetch_prs.py
```

### Search Specific User
Provide the username as a positional argument:
```bash
python fetch_prs.py octocat
```

### Using Flags
```bash
python fetch_prs.py --username google
```

### Advanced Options
- **Include Forked Repos**: By default, the tool ignores repositories you have forked. To include them, use:
  ```bash
  python fetch_prs.py --include-forks
  ```


---

## 💾 Caching Mechanism

To prevent hitting GitHub's API rate limits and to provide near-instant results on subsequent runs, this tool implements a local caching layer:

- **Storage**: Data is stored in the `.cache/` directory.
- **TTL (Time To Live)**: Cache expires after **24 hours**.
- **Efficiency**: Only refetches data from GitHub if the local copy is stale or missing.

---

## 📂 Project Structure

```text
.
├── .cache/               # Local API response storage (auto-generated)
├── .env                  # Your private GitHub token (DO NOT COMMIT)
├── fetch_prs.py          # Main execution script
├── requirements.txt      # Python dependencies
└── README.md             # This documentation
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for any improvements.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Made with ❤️ for developers who love automation.
</p>
