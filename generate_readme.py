from __future__ import annotations

import html
import json
from datetime import datetime, timezone
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


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def badge(label: str, message: str, color: str, *, style: str = "for-the-badge", logo: str | None = None, logo_color: str | None = None) -> str:
    parts = {
        "style": style,
    }
    if logo:
        parts["logo"] = logo
    if logo_color:
        parts["logoColor"] = logo_color

    query = urllib.parse.urlencode(parts)
    label_q = urllib.parse.quote(label)
    message_q = urllib.parse.quote(message)
    return f"https://img.shields.io/badge/{label_q}-{message_q}-{color}?{query}"


def format_timestamp(value: str) -> str:
    if not value:
        return "Recent activity"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return value

    return parsed.strftime("%b %d, %Y · %H:%M UTC")


def render_member_badges(members: list[str], per_row: int = 3) -> str:
    if not members:
        return "*Members will be listed here as the organization grows.*"

    rows = []
    for row in chunked(members, per_row):
        images = []
        for member in row:
            images.append(
                f'<img src="{badge(member, "Member", "111827", logo="github", logo_color="white")}" alt="{member}" />'
            )
        rows.append("\n".join(images))

    return "\n\n<br />\n\n".join(rows)


def fetch_org_events(org_slug: str, per_page: int = 30) -> list[dict]:
    query = urllib.parse.urlencode({"per_page": per_page})
    request = urllib.request.Request(
        f"{GITHUB_API_URL}/orgs/{org_slug}/events?{query}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "code-crew-nexus-readme-generator",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return []


def extract_recent_commits(org_slug: str, limit: int = RECENT_COMMITS_LIMIT) -> list[dict]:
    events = fetch_org_events(org_slug)
    items: list[dict] = []

    for event in events:
        if event.get("type") != "PushEvent":
            continue

        actor = event.get("actor", {})
        payload = event.get("payload", {}) or {}
        repo = event.get("repo", {}) or {}
        repo_full_name = repo.get("name", "")
        repo_name = repo_full_name.split("/", 1)[1] if "/" in repo_full_name else repo_full_name
        branch = (payload.get("ref") or "").split("/")[-1] or "default"
        created_at = event.get("created_at", "")
        event_actor = actor.get("display_login") or actor.get("login") or "Unknown"

        commits = payload.get("commits") or []
        if commits:
            for commit in reversed(commits):
                sha = (commit.get("sha") or payload.get("head") or "").strip()
                if not sha:
                    continue

                author = (commit.get("author") or {}).get("name") or event_actor
                message = (commit.get("message") or "Recent update").splitlines()[0].strip() or "Recent update"
                items.append(
                    {
                        "actor": author,
                        "repo_full_name": repo_full_name,
                        "repo_name": repo_name,
                        "branch": branch,
                        "created_at": created_at,
                        "message": message,
                        "sha": sha[:7],
                        "commit_url": f"https://github.com/{repo_full_name}/commit/{sha}",
                        "repo_url": f"https://github.com/{repo_full_name}",
                    }
                )

                if len(items) >= limit:
                    return items[:limit]
            continue

        head_sha = (payload.get("head") or "").strip()
        if not head_sha:
            continue

        items.append(
            {
                "actor": event_actor,
                "repo_full_name": repo_full_name,
                "repo_name": repo_name,
                "branch": branch,
                "created_at": created_at,
                "message": "Recent update",
                "sha": head_sha[:7],
                "commit_url": f"https://github.com/{repo_full_name}/commit/{head_sha}",
                "repo_url": f"https://github.com/{repo_full_name}",
            }
        )

        if len(items) >= limit:
            return items[:limit]

    return items[:limit]


def render_recent_commits(commits: list[dict]) -> str:
    if not commits:
        return "> Recent commit activity will appear here once public repository pushes are available."

    rows = []
    for row in chunked(commits, 2):
        cells = []
        for commit in row:
            message = html.escape(commit["message"])
            actor = html.escape(commit["actor"])
            repo_name = html.escape(commit["repo_name"])
            branch = html.escape(commit["branch"])
            timestamp = html.escape(format_timestamp(commit["created_at"]))
            sha = html.escape(commit["sha"])
            commit_url = commit["commit_url"]
            repo_url = commit["repo_url"]

            cells.append(
                f"""<td width="50%" valign="top">
<strong>{message}</strong><br />
<sub>{timestamp}</sub>

<br /><br />

<img src="{badge('Committer', actor, '111827', logo='github', logo_color='white')}" alt="{actor}" />
<img src="{badge('Repository', repo_name, '2563EB')}" alt="{repo_name}" />

<br />

<img src="{badge('Branch', branch, '7C3AED')}" alt="{branch}" />
<img src="{badge('Commit', sha, '16A34A')}" alt="{sha}" />

<br /><br />

<a href="{repo_url}">Open repository</a> · <a href="{commit_url}">View commit</a>
</td>"""
            )

        while len(cells) < 2:
            cells.append('<td width="50%" valign="top"></td>')

        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")

    table = "<div align=\"center\">\n\n<table>\n" + "\n".join(rows) + "\n</table>\n\n</div>"
    note = "> This section is generated from recent public push activity across the organization and refreshes whenever the profile README is regenerated."
    return table + "\n\n" + note


def render_repo_link(repo_name: str) -> str:
    repo_name = repo_name.strip()
    if not repo_name:
        return "*Coming soon*"
    return f"[`{repo_name}`](https://github.com/{ORG_SLUG}/{repo_name})"


def render_projects_table(projects: list[dict]) -> str:
    header = "| PROJECT | SUBJECT | TOOLS/LANGUAGES USED | REPOSITORY LINK |"
    divider = "| --- | --- | --- | --- |"

    if not projects:
        row = "| *Coming soon* | *TBD* | *TBD* | *Coming soon* |"
        return "\n".join([header, divider, row])

    rows = []
    for project in projects:
        project_name = (project.get("project") or "TBD").strip() or "TBD"
        subject = (project.get("subject") or "TBD").strip() or "TBD"
        tools = (project.get("tools_languages") or "TBD").strip() or "TBD"
        repo_link = render_repo_link(project.get("repo_name") or "")
        rows.append(f"| **{project_name}** | {subject} | {tools} | {repo_link} |")

    return "\n".join([header, divider, *rows])


def build_readme(members: list[str], projects: list[dict], recent_commits: list[dict]) -> str:
    member_badges = render_member_badges(members)
    projects_table = render_projects_table(projects)
    recent_commits_section = render_recent_commits(recent_commits)

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

> This table is generated from `data/projects.json` so repositories can be added cleanly as the organization grows.

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

This section is intentionally left open for now so it can be filled accurately once repository standards and tool choices are finalized.

### Languages

*To be added.*

### Frameworks

*To be added.*

### Tools

*To be added.*

### What We Optimize For

*To be added.*

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

> The members listed below are generated from `data/members.json`. Repository-level contributors can vary by project, scope, and requirements.

<div align="center">

{member_badges}

</div>

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
    recent_commits = extract_recent_commits(ORG_SLUG)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_readme(members, projects, recent_commits), encoding="utf-8")


if __name__ == "__main__":
    main()
