#!/usr/bin/env python3
"""
Gera o README.md do perfil (bagoduro/bagoduro) puxando dados 100% da API do GitHub.
Nenhum número de stats é digitado manualmente - tudo vem de requests.get() na hora.

Requer a variável de ambiente GITHUB_TOKEN (o Actions já injeta isso sozinho
via secrets.GITHUB_TOKEN, não precisa configurar nada extra).
"""

import os
import sys
import pathlib
import requests

USERNAME = "bagoduro"
TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    print("ERRO: variável de ambiente GITHUB_TOKEN não encontrada.", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{USERNAME}-readme-bot",
}

REST_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"


# ---------------------------------------------------------------------------
# 1. Busca dos dados na API (tudo dinâmico, nada hardcoded)
# ---------------------------------------------------------------------------

def fetch_user():
    r = requests.get(f"{REST_BASE}/users/{USERNAME}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"{REST_BASE}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_total_commits_last_year():
    """Usa a GraphQL API para pegar o total de commits contribuídos no último ano."""
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """
    r = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": {"login": USERNAME}},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    try:
        cc = data["data"]["user"]["contributionsCollection"]
        return cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    except (KeyError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 2. Formatação em texto puro (estilo neofetch, sem cores -
#    o GitHub NAO renderiza codigos ANSI dentro de README.md,
#    entao usamos so espacamento/pontos pra dar o efeito visual)
# ---------------------------------------------------------------------------

LABEL_COL = 17


def fmt(label, value):
    if label:
        pad = label.ljust(LABEL_COL, ".")
        return f"{pad} {value}"
    return f"{' ' * (LABEL_COL + 1)}{value}"


def build_info_block(user, repos, total_commits):
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    repo_count = user.get("public_repos", len(repos))
    followers = user.get("followers", 0)
    following = user.get("following", 0)

    info = []
    info.append("pedro@bagoduro")
    info.append("-" * 42)
    info.append(fmt("Nome", "Pedro Raposo"))
    info.append(fmt("Curso", "Engenharia de Software"))
    info.append(fmt("", "6º Período"))
    info.append(fmt("Linguagens", "Java"))
    info.append(fmt("", "Python"))
    info.append(fmt("", "C#"))
    info.append(fmt("Frameworks", "React"))
    info.append(fmt("Cloud", "AWS"))
    info.append(fmt("Infraestrutura", "Linux"))
    info.append(fmt("", "Ubuntu Server"))
    info.append(fmt("", "VPS"))
    info.append(fmt("Redes", "TCP/IP"))
    info.append(fmt("", "DNS"))
    info.append(fmt("", "HTTP/HTTPS"))
    info.append(fmt("", "SSH"))
    info.append(fmt("", "FTP/SFTP"))
    info.append(fmt("", "VPN"))
    info.append(fmt("", "Firewalls"))
    info.append(fmt("Segurança", "Hardening"))
    info.append(fmt("", "Avaliação de Vulnerabilidades"))
    info.append(fmt("", "Pentest (Ambientes Autorizados)"))
    info.append(fmt("Ferramentas", "Git"))
    info.append(fmt("", "GitHub"))
    info.append(fmt("Interesses", "Backend"))
    info.append(fmt("", "DevOps"))
    info.append(fmt("", "Cloud Computing"))
    info.append(fmt("", "Redes"))
    info.append(fmt("", "Segurança da Informação"))
    info.append("-" * 42)
    info.append(fmt("Contato", "pedroraposo1999@gmail.com"))
    info.append(fmt("Discord", "bagoduro"))
    info.append(fmt("GitHub", f"github.com/{USERNAME}"))
    info.append("")
    info.append("GitHub Stats")
    info.append("-" * 42)
    info.append(fmt("Repositórios", str(repo_count)))
    info.append(fmt("Stars", str(stars)))
    info.append(fmt("Forks", str(forks)))
    info.append(fmt("Seguidores", str(followers)))
    info.append(fmt("Seguindo", str(following)))
    if total_commits is not None:
        info.append(fmt("Commits (1 ano)", str(total_commits)))
    return info


def combine(art_lines, info_lines, pad_width=70, offset=1):
    total = max(len(art_lines), len(info_lines) + offset)
    out = []
    for i in range(total):
        raw_art = art_lines[i] if i < len(art_lines) else ""
        art_padded = raw_art.ljust(pad_width)
        info_idx = i - offset
        info_line = info_lines[info_idx] if 0 <= info_idx < len(info_lines) else ""
        out.append((art_padded + info_line).rstrip())
    return out


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------

def main():
    script_dir = pathlib.Path(__file__).parent
    art_path = script_dir / "art.txt"
    art_lines = art_path.read_text(encoding="utf-8").splitlines()

    user = fetch_user()
    repos = fetch_repos()
    total_commits = fetch_total_commits_last_year()

    info_lines = build_info_block(user, repos, total_commits)
    combined = combine(art_lines, info_lines)

    readme_content = "```\n" + "\n".join(combined) + "\n```\n"

    repo_root = script_dir.parent
    (repo_root / "README.md").write_text(readme_content, encoding="utf-8")
    print("README.md atualizado com sucesso a partir da API do GitHub.")


if __name__ == "__main__":
    main()
