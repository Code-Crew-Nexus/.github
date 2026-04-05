from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timedelta, timezone
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT = ROOT / "profile" / "README.md"

ORG_NAME = "CODE CREW NEXUS"
ORG_SLUG = "Code-Crew-Nexus"
PROFILE_REPO = ".github"
GITHUB_API_URL = "https://api.github.com"
RECENT_COMMITS_LIMIT = 6
REPOS_LIMIT = 25
INDIA_TZ = timezone(timedelta(hours=5, minutes=30), name="IST")
ACRONYMS = {"AI", "ML", "DBMS", "DAA", "OOP", "OOPS", "UI", "UX", "API"}
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

LANGUAGE_ICON_MAP = {
    "Assembly": "https://img.shields.io/badge/ASM-111827?style=for-the-badge&logo=gnuassembler&logoColor=white",
    "C": "https://raw.githubusercontent.com/devicons/devicon/master/icons/c/c-original.svg",
    "C++": "https://raw.githubusercontent.com/devicons/devicon/master/icons/cplusplus/cplusplus-original.svg",
    "CSS": "https://raw.githubusercontent.com/devicons/devicon/master/icons/css3/css3-original.svg",
    "CSS3": "https://raw.githubusercontent.com/devicons/devicon/master/icons/css3/css3-original.svg",
    "HTML": "https://raw.githubusercontent.com/devicons/devicon/master/icons/html5/html5-original.svg",
    "HTML5": "https://raw.githubusercontent.com/devicons/devicon/master/icons/html5/html5-original.svg",
    "Java": "https://raw.githubusercontent.com/devicons/devicon/master/icons/java/java-original.svg",
    "JavaScript": "https://raw.githubusercontent.com/devicons/devicon/master/icons/javascript/javascript-original.svg",
    "Jupyter Notebook": "https://raw.githubusercontent.com/devicons/devicon/master/icons/jupyter/jupyter-original.svg",
    "MySQL": "https://raw.githubusercontent.com/devicons/devicon/master/icons/mysql/mysql-original.svg",
    "Python": "https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg",
    "SQL": "https://raw.githubusercontent.com/devicons/devicon/master/icons/mysql/mysql-original.svg",
    "TypeScript": "https://raw.githubusercontent.com/devicons/devicon/master/icons/typescript/typescript-original.svg",
}

FRAMEWORK_ICON_MAP = {
    "AWT": "https://raw.githubusercontent.com/devicons/devicon/master/icons/java/java-original.svg",
    "Flask": "https://raw.githubusercontent.com/devicons/devicon/master/icons/flask/flask-original.svg",
    "Maven": "https://raw.githubusercontent.com/devicons/devicon/master/icons/maven/maven-original.svg",
    "NumPy": "https://raw.githubusercontent.com/devicons/devicon/master/icons/numpy/numpy-original.svg",
    "Pandas": "https://raw.githubusercontent.com/devicons/devicon/master/icons/pandas/pandas-original.svg",
    "React": "https://raw.githubusercontent.com/devicons/devicon/master/icons/react/react-original.svg",
    "Spring": "https://raw.githubusercontent.com/devicons/devicon/master/icons/spring/spring-original.svg",
}

TOOL_CARDS = [
    ("PyCharm", "https://raw.githubusercontent.com/devicons/devicon/master/icons/pycharm/pycharm-original.svg"),
    ("IntelliJ", "https://raw.githubusercontent.com/devicons/devicon/master/icons/intellij/intellij-original.svg"),
    ("Jupyter", "https://raw.githubusercontent.com/devicons/devicon/master/icons/jupyter/jupyter-original.svg"),
    ("Git", "https://raw.githubusercontent.com/devicons/devicon/master/icons/git/git-original.svg"),
    ("VS Code", "https://raw.githubusercontent.com/devicons/devicon/master/icons/vscode/vscode-original.svg"),
    ("Eclipse", "https://raw.githubusercontent.com/devicons/devicon/master/icons/eclipse/eclipse-original.svg"),
    ("Dev C++", "https://raw.githubusercontent.com/devicons/devicon/master/icons/cplusplus/cplusplus-original.svg"),
]

IGNORED_LANGUAGE_NAMES = {"Makefile"}
SUBJECT_TOPIC_MAP = {
    "ai": "AI",
    "artificial-intelligence": "AI",
    "computer-networks": "CN",
    "csv": "Data Processing",
    "daa": "DAA",
    "database-management": "DBMS",
    "database-management-system": "DBMS",
    "dbms": "DBMS",
    "design-analysis-algorithms": "DAA",
    "machine-learning": "ML",
    "ml": "ML",
    "oop": "OOPs",
    "oops": "OOPs",
    "operating-systems": "OS",
    "os": "OS",
    "pbl": "PBL",
}
SUBJECT_PRIORITY = ["DAA", "DBMS", "OOPs", "OS", "AI", "ML", "CN", "PBL", "Data Processing"]
SUBJECT_NAME_HINTS = {
    "articulation": "DAA",
    "page-replacement": "OS",
    "paging": "OS",
    "tic-tac-toe": "PBL",
}
FRAMEWORK_TOPIC_MAP = {
    "flask": "Flask",
    "maven": "Maven",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "react": "React",
    "spring": "Spring",
}
FRAMEWORK_FILE_MAP = {
    "pom.xml": "Maven",
    "requirements.txt": "Flask",
    "package.json": "React",
    "build.gradle": "Spring",
}
AWT_PATTERN = re.compile(r"\bjava\.awt\b", re.IGNORECASE)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def chunked(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def badge(
    label: str,
    message: str,
    color: str,
    *,
    style: str = "for-the-badge",
    logo: str | None = None,
    logo_color: str | None = None,
) -> str:
    parts = {"style": style}
    if logo:
        parts["logo"] = logo
    if logo_color:
        parts["logoColor"] = logo_color

    query = urllib.parse.urlencode(parts)
    label_q = urllib.parse.quote(label, safe="")
    message_q = urllib.parse.quote(message, safe="")
    return f"https://img.shields.io/badge/{label_q}-{message_q}-{color}?{query}"


def github_json(url: str) -> list[dict] | dict | None:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "code-crew-nexus-readme-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    request = urllib.request.Request(
        url,
        headers=headers,
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def github_text(url: str) -> str | None:
    headers = {
        "Accept": "application/vnd.github.raw+json",
        "User-Agent": "code-crew-nexus-readme-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def format_ist(value: str, *, include_time: bool = True) -> str:
    if not value:
        return "TBD"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(INDIA_TZ)
    except ValueError:
        return value

    if include_time:
        return parsed.strftime("%b %d, %Y · %I:%M %p IST")
    return parsed.strftime("%b %d, %Y")


def humanize_repo_name(name: str) -> str:
    parts = re.split(r"[-_]+", name.strip())
    cleaned = []

    for part in parts:
        if not part:
            continue
        upper = part.upper()
        if upper in ACRONYMS:
            cleaned.append(upper)
        else:
            cleaned.append(part.capitalize())

    return " ".join(cleaned) or name


def normalize_members(members: list[dict] | list[str]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []

    for member in members:
        if isinstance(member, dict):
            name = str(member.get("name") or "").strip()
            designation = str(member.get("designation") or "Organization Member").strip()
        else:
            name = str(member).strip()
            designation = "Organization Member"

        if not name:
            continue

        normalized.append({"name": name, "designation": designation or "Organization Member"})

    return normalized


def render_members_grid(members: list[dict] | list[str], columns: int = 3) -> str:
    members = normalize_members(members)
    if not members:
        return "*Members will be listed here as the organization grows.*"

    rows = []
    for row in chunked(members, columns):
        cells = []
        is_partial_row = len(row) < columns
        left_pad = (columns - len(row)) // 2 if is_partial_row else 0
        right_pad = columns - len(row) - left_pad if is_partial_row else 0

        for _ in range(left_pad):
            cells.append(f'<td align="center" width="{100 // columns}%">&nbsp;</td>')

        for member in row:
            safe_member = html.escape(member["name"])
            safe_designation = html.escape(member["designation"])
            cells.append(
                f"""<td align="center" width="{100 // columns}%">
<strong>{safe_member}</strong><br />
<sub>{safe_designation}</sub>
</td>"""
            )

        while right_pad > 0:
            cells.append(f'<td align="center" width="{100 // columns}%">&nbsp;</td>')
            right_pad -= 1

        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")

    return '<div align="center">\n\n<table>\n' + "\n".join(rows) + "\n</table>\n\n</div>"


def split_project_overrides(projects: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    overrides_by_repo: dict[str, dict] = {}
    manual_rows: list[dict] = []

    for item in projects:
        repo_name = (item.get("repo_name") or "").strip()
        if repo_name:
            overrides_by_repo[repo_name] = item
        else:
            manual_rows.append(item)

    return overrides_by_repo, manual_rows


def fetch_public_repos(org_slug: str) -> list[dict]:
    repos: list[dict] = []
    page = 1

    while True:
        query = urllib.parse.urlencode(
            {
                "type": "public",
                "sort": "updated",
                "per_page": 100,
                "page": page,
            }
        )
        data = github_json(f"{GITHUB_API_URL}/orgs/{org_slug}/repos?{query}")
        if not isinstance(data, list) or not data:
            break

        repos.extend(data)
        if len(data) < 100:
            break
        page += 1

    filtered = [repo for repo in repos if repo.get("name") != PROFILE_REPO]
    filtered.sort(key=lambda repo: repo.get("pushed_at") or "", reverse=True)
    return filtered[:REPOS_LIMIT]


def fetch_latest_commit(repo_full_name: str, branch: str) -> dict | None:
    query = urllib.parse.urlencode({"sha": branch, "per_page": 1})
    data = github_json(f"{GITHUB_API_URL}/repos/{repo_full_name}/commits?{query}")
    if isinstance(data, list) and data:
        return data[0]
    return None


def fetch_repo_details(repo_full_name: str) -> dict:
    data = github_json(f"{GITHUB_API_URL}/repos/{repo_full_name}")
    return data if isinstance(data, dict) else {}


def fetch_repo_languages(repo_full_name: str) -> dict[str, int]:
    data = github_json(f"{GITHUB_API_URL}/repos/{repo_full_name}/languages")
    return data if isinstance(data, dict) else {}


def fetch_root_entries(repo_full_name: str, branch: str) -> list[dict]:
    query = urllib.parse.urlencode({"ref": branch})
    data = github_json(f"{GITHUB_API_URL}/repos/{repo_full_name}/contents?{query}")
    return data if isinstance(data, list) else []


def fetch_readme_text(repo_full_name: str) -> str:
    text = github_text(f"{GITHUB_API_URL}/repos/{repo_full_name}/readme")
    return text or ""


def fetch_repo_branches(repo_full_name: str) -> list[str]:
    branches: list[str] = []
    page = 1

    while True:
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        data = github_json(f"{GITHUB_API_URL}/repos/{repo_full_name}/branches?{query}")
        if not isinstance(data, list) or not data:
            break

        for branch in data:
            name = str(branch.get("name") or "").strip()
            if name and name not in branches:
                branches.append(name)

        if len(data) < 100:
            break
        page += 1

    return branches


def infer_subject(repo_name: str, topics: list[str]) -> str:
    found_subjects: list[str] = []

    for topic in topics:
        mapped = SUBJECT_TOPIC_MAP.get(topic.lower())
        if mapped and mapped not in found_subjects:
            found_subjects.append(mapped)

    for subject in SUBJECT_PRIORITY:
        if subject in found_subjects:
            return subject

    lowered = repo_name.lower()
    for hint, mapped in SUBJECT_NAME_HINTS.items():
        if hint in lowered:
            return mapped

    for key, mapped in SUBJECT_TOPIC_MAP.items():
        if key in lowered:
            return mapped

    return "TBD"


def format_language_stack(language_map: dict[str, int]) -> str:
    names = [name for name in language_map if name not in IGNORED_LANGUAGE_NAMES]
    return ", ".join(names[:3]) if names else "TBD"


def resolve_stack(language_map: dict[str, int], primary_language: str) -> str:
    stack = format_language_stack(language_map)
    if stack != "TBD":
        return stack
    return primary_language.strip() if primary_language and primary_language.strip() else "TBD"


def format_branch_list(branches: list[str], default_branch: str) -> str:
    cleaned = [branch.strip() for branch in branches if branch and branch.strip()]
    if not cleaned and default_branch:
        cleaned = [default_branch.strip()]
    if not cleaned:
        return "TBD"
    return "<br />".join(f"`{html.escape(branch)}`" for branch in cleaned)


def detect_frameworks(repo: dict, readme_text: str = "") -> list[str]:
    detected: list[str] = []
    topics = [str(topic).strip() for topic in repo.get("topics", []) if str(topic).strip()]
    root_names = {str(entry.get("name") or "").strip().lower() for entry in repo.get("root_entries", [])}
    readme_lower = readme_text.lower()

    for topic in topics:
        framework = FRAMEWORK_TOPIC_MAP.get(topic.lower())
        if framework and framework not in detected:
            detected.append(framework)

    for file_name, framework in FRAMEWORK_FILE_MAP.items():
        if file_name.lower() in root_names and framework not in detected:
            detected.append(framework)

    if AWT_PATTERN.search(readme_text) and "AWT" not in detected:
        detected.append("AWT")
    elif "awt" in readme_lower and "AWT" not in detected:
        detected.append("AWT")

    return detected


def enrich_repos(repos: list[dict]) -> list[dict]:
    enriched: list[dict] = []

    for repo in repos:
        repo_name = str(repo.get("name") or "").strip()
        repo_full_name = str(repo.get("full_name") or "").strip()
        branch = str(repo.get("default_branch") or "main").strip()
        if not repo_name or not repo_full_name:
            continue

        details = fetch_repo_details(repo_full_name)
        merged = {**repo, **details} if details else dict(repo)
        merged["language_map"] = fetch_repo_languages(repo_full_name)
        merged["branches"] = fetch_repo_branches(repo_full_name)
        merged["root_entries"] = fetch_root_entries(repo_full_name, branch)
        merged["readme_text"] = fetch_readme_text(repo_full_name)
        enriched.append(merged)

    return enriched


def build_project_rows(projects: list[dict], repos: list[dict]) -> list[dict]:
    overrides_by_repo, manual_rows = split_project_overrides(projects)
    rows: list[dict] = []

    for repo in repos:
        repo_name = repo.get("name", "").strip()
        if not repo_name:
            continue

        override = overrides_by_repo.get(repo_name, {})
        topics = [str(topic).strip() for topic in repo.get("topics", []) if str(topic).strip()]
        language_map = repo.get("language_map") or {}
        default_branch = (repo.get("default_branch") or "main").strip()
        branches = repo.get("branches") or []
        description = (override.get("description") or repo.get("description") or "Academic repository under active development.").strip()
        rows.append(
            {
                "project": (override.get("project") or humanize_repo_name(repo_name)).strip(),
                "subject": (override.get("subject") or infer_subject(repo_name, topics)).strip(),
                "tools_languages": (override.get("tools_languages") or resolve_stack(language_map, repo.get("language") or "")).strip(),
                "description": description,
                "last_commit": format_ist(repo.get("pushed_at", ""), include_time=False),
                "branches": format_branch_list(branches, default_branch),
                "repo_name": repo_name,
                "repo_url": repo.get("html_url") or f"https://github.com/{ORG_SLUG}/{repo_name}",
            }
        )

    if rows:
        return rows

    fallback_rows: list[dict] = []
    for item in manual_rows:
        fallback_rows.append(
            {
                "project": (item.get("project") or "Coming Soon").strip(),
                "subject": (item.get("subject") or "TBD").strip(),
                "tools_languages": (item.get("tools_languages") or "TBD").strip(),
                "description": (item.get("description") or "Project details will appear here once the repository is added.").strip(),
                "last_commit": "TBD",
                "branches": "TBD",
                "repo_name": "",
                "repo_url": "",
            }
        )

    return fallback_rows or [
        {
            "project": "Coming Soon",
            "subject": "TBD",
            "tools_languages": "TBD",
            "description": "Project details will appear here once the repository is added.",
            "last_commit": "TBD",
            "branches": "TBD",
            "repo_name": "",
            "repo_url": "",
        }
    ]


def render_projects_table(project_rows: list[dict]) -> str:
    header = "| PROJECT | SUBJECT | STACK | DESCRIPTION | LAST UPDATE | BRANCHES | REPOSITORY |"
    divider = "| --- | --- | --- | --- | --- | --- | --- |"
    rows = []

    for item in project_rows:
        repo_name = item["repo_name"]
        if repo_name and item["repo_url"]:
            repo_link = f"[`{repo_name}`]({item['repo_url']})"
        else:
            repo_link = "*Coming soon*"

        rows.append(
            f"| **{item['project']}** | {item['subject']} | {item['tools_languages']} | "
            f"{item['description']} | {item['last_commit']} | {item['branches']} | {repo_link} |"
        )

    return "\n".join([header, divider, *rows])


def build_recent_commits(repos: list[dict], limit: int = RECENT_COMMITS_LIMIT) -> list[dict]:
    items: list[dict] = []

    for repo in repos:
        repo_name = repo.get("name", "").strip()
        repo_full_name = repo.get("full_name", "").strip()
        branch = (repo.get("default_branch") or "main").strip()
        repo_url = repo.get("html_url") or f"https://github.com/{ORG_SLUG}/{repo_name}"

        if not repo_name or not repo_full_name:
            continue

        latest = fetch_latest_commit(repo_full_name, branch)
        if not latest:
            continue

        commit_info = latest.get("commit", {}) or {}
        committer_info = commit_info.get("committer", {}) or {}
        author_info = commit_info.get("author", {}) or {}
        actor = (
            (latest.get("author") or {}).get("login")
            or committer_info.get("name")
            or author_info.get("name")
            or "Unknown"
        )
        commit_date = committer_info.get("date") or author_info.get("date") or ""
        message = (commit_info.get("message") or "Recent update").splitlines()[0].strip() or "Recent update"
        sha = (latest.get("sha") or "")[:7]

        items.append(
            {
                "message": message,
                "actor": actor,
                "repo_name": repo_name,
                "repo_url": repo_url,
                "branch": branch,
                "sha": sha,
                "commit_url": latest.get("html_url") or f"{repo_url}/commit/{latest.get('sha', '')}",
                "committed_at": commit_date,
            }
        )

    items.sort(key=lambda item: item.get("committed_at") or "", reverse=True)
    return items[:limit]


def render_recent_commits(commits: list[dict]) -> str:
    if not commits:
        return "> Recent commit activity will appear here once public repositories in the organization start receiving commits."

    rows = []
    for row in chunked(commits, 2):
        cells = []
        for commit in row:
            message = html.escape(commit["message"])
            actor = html.escape(commit["actor"])
            repo_name = html.escape(commit["repo_name"])
            branch = html.escape(commit["branch"])
            timestamp = html.escape(format_ist(commit["committed_at"]))
            sha = html.escape(commit["sha"])
            repo_url = commit["repo_url"]
            commit_url = commit["commit_url"]

            cells.append(
                f"""<td width="50%" valign="top">
<strong><a href="{commit_url}">{message}</a></strong><br />
<sub>{timestamp}</sub>

<br /><br />

<strong>Repository:</strong> <a href="{repo_url}">{repo_name}</a><br />
<strong>Committed by:</strong> {actor}<br />
<strong>Branch:</strong> <code>{branch}</code><br />
<strong>Commit:</strong> <code>{sha}</code>
</td>"""
            )

        while len(cells) < 2:
            cells.append('<td width="50%" valign="top">&nbsp;</td>')

        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")

    return (
        '<div align="center">\n\n<table>\n'
        + "\n".join(rows)
        + '\n</table>\n\n</div>\n\n'
        + "> This section is generated from the latest public commits across organization repositories and is shown in Indian Standard Time."
    )


def icon_for(name: str, icon_map: dict[str, str]) -> str:
    if name in icon_map:
        return icon_map[name]
    return badge(name, "Stack", "111827", logo="github", logo_color="white")


def render_icon_table(items: list[tuple[str, str]], columns: int = 5) -> str:
    if not items:
        return "*No items detected yet.*"

    rows = []
    for row in chunked(items, columns):
        cells = []
        is_partial_row = len(row) < columns
        left_pad = (columns - len(row)) // 2 if is_partial_row else 0
        right_pad = columns - len(row) - left_pad if is_partial_row else 0

        for _ in range(left_pad):
            cells.append(f'<td align="center" width="{100 // columns}%">&nbsp;</td>')

        for name, icon_url in row:
            safe_name = html.escape(name)
            cells.append(
                f"""<td align="center" width="{100 // columns}%">
<img src="{icon_url}" alt="{safe_name}" width="64" height="64" /><br />
<strong>{safe_name}</strong>
</td>"""
            )

        while right_pad > 0:
            cells.append(f'<td align="center" width="{100 // columns}%">&nbsp;</td>')
            right_pad -= 1

        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")

    return '<div align="center">\n\n<table>\n' + "\n".join(rows) + "\n</table>\n\n</div>"


def build_tech_specs(repos: list[dict]) -> dict[str, list]:
    languages_seen: list[str] = []
    frameworks_seen: list[str] = []

    for repo in repos:
        language_map = repo.get("language_map") or {}
        for language in language_map:
            if language in IGNORED_LANGUAGE_NAMES or language in languages_seen:
                continue
            languages_seen.append(language)

        for framework in detect_frameworks(repo, repo.get("readme_text", "")):
            if framework not in frameworks_seen:
                frameworks_seen.append(framework)

    if not languages_seen:
        primary_languages = [repo.get("language") for repo in repos if repo.get("language")]
        for language in primary_languages:
            if language not in languages_seen and language not in IGNORED_LANGUAGE_NAMES:
                languages_seen.append(language)

    language_cards = [(language, icon_for(language, LANGUAGE_ICON_MAP)) for language in languages_seen[:10]]
    framework_cards = [(framework, icon_for(framework, FRAMEWORK_ICON_MAP)) for framework in frameworks_seen[:8]]

    return {
        "language_cards": language_cards,
        "framework_cards": framework_cards,
        "tool_cards": TOOL_CARDS,
    }


def render_tech_specs(repos: list[dict]) -> str:
    tech_specs = build_tech_specs(repos)
    languages_block = render_icon_table(tech_specs["language_cards"], columns=5)
    frameworks_block = (
        render_icon_table(tech_specs["framework_cards"], columns=4)
        if tech_specs["framework_cards"]
        else "*No frameworks have been detected from the current public repositories yet.*"
    )
    tools_block = render_icon_table(tech_specs["tool_cards"], columns=5)

    return f"""This section is generated from the organization's current public repositories wherever possible, while the core collaboration tools remain intentionally standardized.

### Languages

{languages_block}

### Frameworks

{frameworks_block}

### Tools

{tools_block}

### What We Optimize For

- Clean repository structure and readable implementation.
- Documentation that helps peers, faculty, and reviewers understand the work quickly.
- Project setups that stay reproducible as repositories keep growing.
- Practical tools that support collaboration across different subjects and workflows.

> Languages and frameworks are inferred from the organization's public repositories. Tools are kept as a standard baseline for the team workspace."""


def build_readme(members: list[dict] | list[str], projects: list[dict], repos: list[dict], recent_commits: list[dict]) -> str:
    members_grid = render_members_grid(members)
    project_rows = build_project_rows(projects, repos)
    projects_table = render_projects_table(project_rows)
    recent_commits_section = render_recent_commits(recent_commits)
    tech_specs_section = render_tech_specs(repos)

    return f'''<!-- THIS FILE IS GENERATED. Edit data/members.json and data/projects.json, then run python generate_readme.py. -->

<div align="center">

# {ORG_NAME}

### Professional Organization Space for Academic Projects, Subject Repositories, and Structured Innovation

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22&duration=2800&pause=900&color=0EA5E9&center=true&vCenter=true&repeat=true&width=940&lines=Building+academic+projects+with+professional+intent;Maintaining+subject-based+repositories+with+clarity;Encouraging+structured+collaboration+and+innovation;Turning+project+work+into+portfolio-ready+outcomes" alt="Typing SVG" />

<br />

<p><strong>CODE CREW NEXUS</strong> is a professional GitHub organization designed to centralize collaborative academic work, project-driven learning, and innovation-focused development.</p>

<br />

<a href="https://github.com/{ORG_SLUG}"><img src="{badge('Organization', ORG_NAME, '111827', logo='github', logo_color='white')}" alt="Organization" /></a>
<img src="{badge('Direction', 'Innovation Driven', '0EA5E9')}" alt="Direction" />
<img src="{badge('Standard', 'Professional', '16A34A')}" alt="Professional Standard" />
<img src="{badge('Profile', 'Actively Maintained', 'F97316')}" alt="Profile Status" />

<br />

<img src="https://img.shields.io/github/repo-size/{ORG_SLUG}/{PROFILE_REPO}?style=for-the-badge&color=2563EB" alt="Repository Size" />
<img src="https://img.shields.io/github/last-commit/{ORG_SLUG}/{PROFILE_REPO}?style=for-the-badge&color=7C3AED" alt="Last Commit" />
<img src="{badge('Status', 'Active', '22C55E')}" alt="Project Status" />
<img src="{badge('Theme', 'Innovation', 'E11D48')}" alt="Theme" />

<br />

<img src="https://img.shields.io/github/stars/{ORG_SLUG}/{PROFILE_REPO}?style=social" alt="GitHub Stars" />
<img src="https://img.shields.io/github/forks/{ORG_SLUG}/{PROFILE_REPO}?style=social" alt="GitHub Forks" />
<img src="https://img.shields.io/github/watchers/{ORG_SLUG}/{PROFILE_REPO}?style=social" alt="GitHub Watchers" />

</div>

<br />

```text
Focus      : Academic collaboration, repository quality, structured documentation
Approach   : Professional presentation, reproducible work, innovation-led execution
Positioning: A durable project hub for peers, faculty, and future opportunities
```

---
## Purpose

**CODE CREW NEXUS** exists to bring project work into one organized, durable, and high-clarity space.

This organization is designed for:

- academic projects with real-world thinking,
- subject-based repositories that stay easy to navigate,
- shared experiments and implementation-driven learning,
- and portfolio-quality presentation for peers, faculty, and recruiters.

We want every repository here to feel intentional, readable, and worth revisiting.

---
## Overview

This organization is built to support serious collaboration and stronger project visibility.

Instead of treating repositories as isolated submissions, **CODE CREW NEXUS** serves as a long-term project hub where code, documentation, reports, diagrams, and implementation quality all matter equally.

> More than a GitHub organization, this is a structured workspace for disciplined learning, stronger execution, and visible growth.

---
## Vision & Mission

- Build impactful academic projects with real-world relevance.
- Learn collaboratively and share knowledge across subjects.
- Maintain professional standards in code, documentation, and teamwork.
- Showcase collective work as a strong portfolio for recruiters, peers, and faculty.

Our mission is to create work that reflects both technical seriousness and team maturity.

---
## Activities

- Create subject-based repositories for areas like DAA, DBMS, OOPs, AI/ML, and more.
- Collaborate in smaller groups depending on project size, scope, and requirements.
- Document projects with structured reports, diagrams, implementation notes, and clear logic.
- Review each other's work for readability, reproducibility, and clarity.
- Maintain a central hub that combines innovation, teamwork, and professional presentation.

---
## Ambition

This organization is more than just a GitHub space. It is a collaboration-first environment shaped by ambition, growth, and unity.

We are building it as a foundation for:

- stronger project execution,
- better ownership and accountability,
- cleaner technical presentation,
- and long-term growth as learners and future professionals.

Every project added here should strengthen the story of a team that builds with intent and improves together.

---
## Project Directory

{projects_table}

> This directory is generated from the organization's public repositories and enriched by optional overrides in `data/projects.json`.

---
## Recent Commits

{recent_commits_section}

---
## Repository Structure

- Each repository represents a subject, project, or focused experiment.
- Teams can be assigned based on project requirements and contribution needs.
- Repositories should include code, documentation, and real-world examples wherever relevant.

### Typical flow

`Idea -> Planning -> Implementation -> Documentation -> Review -> Showcase`

---
## Innovation Roadmap

- [ ] Flagship project spotlight
- [ ] Expanded subject repository lineup
- [ ] Shared documentation standard
- [ ] Unified project showcase format

---
## Tech Specs & Tools

{tech_specs_section}

---
## Why This Org Stands Out

| Focus Area | What It Looks Like |
| --- | --- |
| **Team-Based Learning** | Knowledge moves across the group instead of staying isolated inside individual repositories. |
| **Documentation Depth** | Reports, diagrams, and implementation notes are treated as part of the project, not as an afterthought. |
| **Professional Presentation** | Repositories are organized to look polished, understandable, and recruiter-friendly. |
| **Shared Ownership** | Projects are strengthened through accountability, review, and collaboration. |

---
## How We Work

| Approach | In Practice |
| --- | --- |
| **Plan with intent** | We organize projects before building so the final output feels structured and complete. |
| **Build collaboratively** | Work is distributed thoughtfully to match scope, timelines, and strengths. |
| **Review for clarity** | We care about whether a project can be understood, reproduced, and showcased well. |
| **Keep improving** | Each repository is a chance to raise our standards in code, docs, and teamwork. |

---
## Members

{members_grid}

> This section is generated from `data/members.json` and is presented as the current organization member list for the profile.

---
## Tagline

**Forging ideas into impactful projects.**  
**Where teamwork meets innovation.**  
**Built for collaboration, driven by ambition.**

---
## Closing Note

**CODE CREW NEXUS** is our shared space for turning ideas into outcomes, assignments into achievements, and collaboration into something lasting.

As new repositories take shape, this profile will grow into a durable reflection of our work, our standards, and our collective momentum.
'''


def main() -> None:
    members = load_json(DATA_DIR / "members.json")
    projects = load_json(DATA_DIR / "projects.json")
    fetched_repos = fetch_public_repos(ORG_SLUG)
    if not fetched_repos and OUTPUT.exists():
        return

    repos = enrich_repos(fetched_repos)
    recent_commits = build_recent_commits(repos)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_readme(members, projects, repos, recent_commits), encoding="utf-8")


if __name__ == "__main__":
    main()
