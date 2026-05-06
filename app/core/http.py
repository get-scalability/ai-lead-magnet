from bs4 import BeautifulSoup
import httpx


_SCRAPE_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ScalabilityBot/1.0)"}
_SCRAPE_CHAR_LIMIT = 3000


async def scrape_domain(domain: str) -> str:
    """Fetch a domain homepage and return cleaned text (max 3k chars).

    Returns empty string on any failure — callers treat this as a soft error.
    """
    url = domain if domain.startswith("http") else f"https://{domain}"
    try:
        async with httpx.AsyncClient(
            timeout=10.0, headers=_SCRAPE_HEADERS, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)[:_SCRAPE_CHAR_LIMIT]
    except Exception:  # noqa: BLE001
        return ""
