import os
import re
import json
import time
import hashlib
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langdetect import detect as lang_detect
from readability import Document
import trafilatura
import urllib.robotparser as robotparser

# CrewAI BaseTool
from crewai.tools import BaseTool

# -------------------------
# Back-compat shim:
# Older/newer CrewAI builds sometimes expect `.to_tool()`.
# If it's missing, provide a no-op implementation that returns self.
# -------------------------
if not hasattr(BaseTool, "to_tool"):
    def _to_tool(self):  # noqa: D401
        """Return self (compat shim)."""
        return self
    BaseTool.to_tool = _to_tool  # type: ignore[attr-defined]

# =========================
# CONFIGURATION
# =========================
UA_DEFAULT = os.getenv("SCRAPER_USER_AGENT", "MarketMindBot/1.0 (+https://example.com/bot)")
CACHE_DIR = os.getenv("SCRAPER_CACHE_DIR", ".cache")
TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT_SECS", "20"))
RESPECT_ROBOTS = os.getenv("SCRAPER_RESPECT_ROBOTS", "true").lower() == "true"

os.makedirs(CACHE_DIR, exist_ok=True)

# =========================
# HELPERS
# =========================
def _cache_key_for(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def _save_cache(url: str, payload: dict) -> None:
    fp = os.path.join(CACHE_DIR, _cache_key_for(url) + ".json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def _load_cache(url: str):
    fp = os.path.join(CACHE_DIR, _cache_key_for(url) + ".json")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _clean_text(txt: str) -> str:
    return re.sub(r"\s+", " ", (txt or "").strip())

def _is_probably_article(html: str) -> bool:
    score = html.count("") + html.count("schema.org/Article")
    return score >= 3

def _respect_robots(url: str) -> bool:
    if not RESPECT_ROBOTS:
        return True
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(UA_DEFAULT, url)
    except Exception:
        # If robots is unreachable, be permissive
        return True

# =========================
# FETCHER
# =========================
class FetchError(Exception):
    pass

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(FetchError),
)
def _fetch(url: str) -> tuple[str, str]:
    if not url.lower().startswith(("http://", "https://")):
        raise FetchError("Invalid URL scheme")

    if not _respect_robots(url):
        raise FetchError("Blocked by robots.txt")

    cached = _load_cache(url)
    if cached:
        return cached.get("final_url", url), cached.get("html", "")

    headers = {"User-Agent": UA_DEFAULT, "Accept": "text/html,application/xhtml+xml"}
    try:
        with httpx.Client(follow_redirects=True, timeout=TIMEOUT, headers=headers) as client:
            r = client.get(url)
            if r.status_code >= 400:
                raise FetchError(f"HTTP {r.status_code}")
            html = r.text
            final_url = str(r.url)
            _save_cache(url, {"final_url": final_url, "html": html})
            return final_url, html
    except Exception as e:
        raise FetchError(str(e))

# =========================
# EXTRACTION
# =========================
def extract_main_content(url: str, html: str) -> dict:
    title, text = "", ""
    try:
        doc = Document(html)
        title = doc.short_title() or ""
        content_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(content_html, "lxml")
        text = _clean_text(soup.get_text(" "))
    except Exception:
        pass

    if not text or len(text) < 300:
        try:
            t_text = trafilatura.extract(html, include_comments=False, include_links=False) or ""
            if len(t_text) > len(text):
                text = _clean_text(t_text)
        except Exception:
            pass

    if not text or len(text) < 200:
        try:
            soup_full = BeautifulSoup(html, "lxml")
            for tag in soup_full(["script", "style", "nav", "aside", "footer", "header"]):
                tag.decompose()
            text = _clean_text(soup_full.get_text(" "))
            if not title:
                title_tag = soup_full.find("title")
                title = _clean_text(title_tag.text if title_tag else "")
        except Exception:
            pass

    links = []
    try:
        soup_links = BeautifulSoup(html, "lxml")
        for a in soup_links.find_all("a", href=True):
            absu = urljoin(url, a["href"])
            links.append(absu)

        seen = set()
        dedup = []
        base_host = urlparse(url).netloc
        for l in links:
            key = l.split("#")[0]
            if key not in seen:
                seen.add(key)
                dedup.append({"url": l, "same_domain": urlparse(l).netloc == base_host})
        links = dedup[:200]
    except Exception:
        links = []

    try:
        language = lang_detect(text[:2000]) if text else ""
    except Exception:
        language = ""

    return {
        "title": title,
        "text": text,
        "language": language,
        "links": links,
        "is_article_like": _is_probably_article(html),
    }

# =========================
# TOOLS
# =========================
class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web via Serper.dev and return top organic results."

    def _run(self, query: str) -> str:
        api_key = os.getenv("SERPER_API_KEY", "")
        if not api_key:
            return json.dumps({"results": []})
        import requests
        try:
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
            payload = {"q": query, "num": 10}
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            data = r.json()
            out = [
                {
                    "title": it.get("title", ""),
                    "snippet": it.get("snippet", ""),
                    "url": it.get("link") or it.get("url", ""),
                }
                for it in data.get("organic", [])[:10]
            ]
            return json.dumps({"results": out}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"results": [], "error": str(e)})

class WebScrapeTool(BaseTool):
    name: str = "web_scrape"
    description: str = "Scrape a webpage and return title, text, language, and links JSON."

    def _run(self, url: str) -> str:
        final_url, html = _fetch(url)
        data = extract_main_content(final_url, html)
        data["url"] = final_url
        return json.dumps(data, ensure_ascii=False)

class FallbackSearchTool(BaseTool):
    name: str = "fallback_search"
    description: str = "DuckDuckGo HTML fallback search (no API key needed)."

    def _run(self, query: str) -> str:
        try:
            ddg = "https://duckduckgo.com/html/"
            headers = {"User-Agent": UA_DEFAULT}
            resp = httpx.get(ddg, params={"q": query}, headers=headers, timeout=TIMEOUT)
            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for r in soup.select(".result__body")[:10]:
                a = r.select_one(".result__a")
                snip = r.select_one(".result__snippet")
                if a and a.get("href"):
                    results.append({
                        "title": _clean_text(a.get_text(" ")),
                        "snippet": _clean_text(snip.get_text(" ") if snip else ""),
                        "url": a.get("href"),
                    })
            return json.dumps({"results": results}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"results": [], "error": str(e)})

class FileReadTool(BaseTool):
    name: str = "file_read"
    description: str = "Read text/markdown files from disk (UTF-8)."

    def _run(self, path: str) -> str:
        path = path.strip()
        if not os.path.exists(path):
            return f"[file_read] File not found: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
