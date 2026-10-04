"""
Rewrites the projects section of your GitHub profile README with all your
public repositories. Runs inside a GitHub Action (see update-readme.yml).

Only the text between these two markers in README.md is replaced:
    <!-- PROJECTS:START -->
    <!-- PROJECTS:END -->
Everything else in your README stays exactly as you wrote it.
"""

import json
import os
import re
import urllib.request
from datetime import datetime

OWNER = os.environ["GITHUB_REPOSITORY_OWNER"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README = "README.md"
START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"

# Settings you can change
SKIP_FORKS = True
SKIP_ARCHIVED = True
SKIP_REPOS = {OWNER.lower()}  # the profile repo itself; add other names here


def fetch_repos():
    repos, page = [], 1
    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&sort=updated&per_page=100&page={page}"
        )
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if TOKEN:
            req.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(req) as resp:
            batch = json.load(resp)
        if not batch:
            return repos
        repos.extend(batch)
        page += 1


def keep(repo):
    if repo["private"]:
        return False
    if SKIP_FORKS and repo["fork"]:
        return False
    if SKIP_ARCHIVED and repo["archived"]:
        return False
    return repo["name"].lower() not in SKIP_REPOS


def build_table(repos):
    lines = [
        "| Project | Description | Language | ⭐ | Updated |",
        "|---|---|---|---|---|",
    ]
    for r in repos:
        desc = (r["description"] or "").replace("|", "\\|")
        updated = datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y")
        lines.append(
            f"| [{r['name']}]({r['html_url']}) | {desc} | {r['language'] or ''} "
            f"| {r['stargazers_count']} | {updated} |"
        )
    return "\n".join(lines)


def main():
    repos = [r for r in fetch_repos() if keep(r)]
    section = f"{START}\n{build_table(repos)}\n{END}"

    with open(README, encoding="utf-8") as f:
        text = f.read()

    if START in text and END in text:
        text = re.sub(
            re.escape(START) + r".*?" + re.escape(END), section, text, flags=re.DOTALL
        )
    else:
        text = text.rstrip() + "\n\n## Projects\n\n" + section + "\n"

    with open(README, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Listed {len(repos)} repositories.")


if __name__ == "__main__":
    main()
