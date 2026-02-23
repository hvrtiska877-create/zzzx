from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass


USER_AGENT = "SMART/0.2 (+https://example.local)"


@dataclass
class ResearchSnippet:
    source: str
    title: str
    url: str
    snippet: str


class ResearchClient:
    """Collects lightweight public web context from free/public endpoints."""

    def __init__(self, timeout_sec: float = 10.0) -> None:
        self.timeout_sec = timeout_sec
        self.google_api_key = os.getenv("SMART_GOOGLE_API_KEY")
        self.google_cx = os.getenv("SMART_GOOGLE_CX")

    def _get_json(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def search_google(self, query: str, limit: int = 3) -> list[ResearchSnippet]:
        """Google Programmable Search (has free tier, requires API key + CX)."""
        if not self.google_api_key or not self.google_cx:
            raise ValueError("SMART_GOOGLE_API_KEY and SMART_GOOGLE_CX are required for Google search")

        q = urllib.parse.quote(query)
        url = (
            "https://www.googleapis.com/customsearch/v1"
            f"?key={self.google_api_key}&cx={self.google_cx}&q={q}&num={limit}"
        )
        payload = self._get_json(url)
        items = payload.get("items", [])
        out: list[ResearchSnippet] = []
        for item in items:
            out.append(
                ResearchSnippet(
                    source="google",
                    title=item.get("title", "unknown"),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                )
            )
        return out

    def search_github(self, query: str, limit: int = 3) -> list[ResearchSnippet]:
        q = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
        payload = self._get_json(url)
        items = payload.get("items", [])
        out: list[ResearchSnippet] = []
        for item in items:
            out.append(
                ResearchSnippet(
                    source="github",
                    title=item.get("full_name", "unknown"),
                    url=item.get("html_url", ""),
                    snippet=item.get("description", "") or "No description",
                )
            )
        return out

    def search_reddit(self, query: str, limit: int = 3) -> list[ResearchSnippet]:
        q = urllib.parse.quote(query)
        url = f"https://www.reddit.com/search.json?q={q}&limit={limit}&sort=relevance&t=year"
        payload = self._get_json(url)
        children = payload.get("data", {}).get("children", [])
        out: list[ResearchSnippet] = []
        for child in children:
            data = child.get("data", {})
            out.append(
                ResearchSnippet(
                    source="reddit",
                    title=data.get("title", "unknown"),
                    url=f"https://reddit.com{data.get('permalink', '')}",
                    snippet=(data.get("selftext", "") or "")[:240],
                )
            )
        return out

    def search_duckduckgo(self, query: str, limit: int = 3) -> list[ResearchSnippet]:
        q = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={q}&format=json&no_redirect=1&no_html=1"
        payload = self._get_json(url)
        out: list[ResearchSnippet] = []

        abstract = payload.get("AbstractText", "")
        if abstract:
            out.append(
                ResearchSnippet(
                    source="duckduckgo",
                    title=payload.get("Heading", "DuckDuckGo"),
                    url=payload.get("AbstractURL", ""),
                    snippet=abstract,
                )
            )

        for topic in payload.get("RelatedTopics", []):
            if isinstance(topic, dict) and "Text" in topic:
                out.append(
                    ResearchSnippet(
                        source="duckduckgo",
                        title=topic.get("Text", "topic")[:80],
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", ""),
                    )
                )
            if len(out) >= limit:
                break

        return out[:limit]

    def gather(self, query: str, limit_per_source: int = 3) -> list[ResearchSnippet]:
        snippets: list[ResearchSnippet] = []
        for getter in (self.search_google, self.search_reddit, self.search_github, self.search_duckduckgo):
            try:
                snippets.extend(getter(query, limit_per_source))
            except Exception as exc:  # noqa: BLE001
                snippets.append(
                    ResearchSnippet(
                        source="system",
                        title=f"{getter.__name__} unavailable",
                        url="",
                        snippet=str(exc),
                    )
                )
        return snippets
