import webbrowser
import urllib.parse

from registry.resolver import resolve_website


def open_website(url: str) -> str:
    try:
        webbrowser.open(url)
        return f"Abrindo {url}"
    except Exception as e:
        return f"Erro ao abrir site: {e}"


def open_any_website(target: str) -> str:
    target = target.strip()

    if not target:
        return "Site inválido."

    site_key, site_data = resolve_website(target)

    if site_data:
        return open_website(site_data["url"])

    return f"Site fora do registry: {target}"


def search_website(target: str, query: str) -> str:
    target = target.strip()
    query = query.strip()

    if not query:
        return "Consulta vazia."

    site_key, site_data = resolve_website(target)

    if not site_data:
        return f"Pesquisa no site '{target}' não é suportada."

    search_url = site_data.get("search_url")

    if not search_url:
        return f"O site '{site_key}' não tem pesquisa configurada."

    encoded_query = urllib.parse.quote_plus(query)
    url = search_url.format(query=encoded_query)

    try:
        webbrowser.open(url)
        return f"Pesquisando '{query}' em {site_key}."
    except Exception as e:
        return f"Erro ao pesquisar em {site_key}: {e}"
