from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx


class OpenAPIClient:
    """Clients for keyless, free/open public APIs."""

    def __init__(self, timeout_sec: float = 10.0) -> None:
        self.timeout_sec = timeout_sec

    def wikipedia_search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        if not query.strip():
            raise RuntimeError("query is required")
        params: dict[str, Any] = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": limit,
            "origin": "*",
        }
        with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
            response = client.get("https://en.wikipedia.org/w/api.php", params=params)
            response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])
        return [
            {
                "title": str(item.get("title", "")),
                "snippet": str(item.get("snippet", "")),
                "url": f"https://en.wikipedia.org/wiki/{str(item.get('title', '')).replace(' ', '_')}",
            }
            for item in results
        ]

    def open_meteo_forecast(self, location: str) -> dict[str, Any]:
        if not location.strip():
            raise RuntimeError("location is required")
        with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
            geo = client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "language": "en", "format": "json"},
            )
            geo.raise_for_status()
            results = geo.json().get("results") or []
            if not results:
                raise RuntimeError(f"Location not found: {location}")
            place = results[0]
            forecast = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "timezone": "auto",
                },
            )
            forecast.raise_for_status()
        payload = forecast.json()
        return {
            "location": {
                "name": place.get("name"),
                "country": place.get("country"),
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
            },
            "current": payload.get("current", {}),
            "daily": payload.get("daily", {}),
        }

    def arxiv_search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        if not query.strip():
            raise RuntimeError("query is required")
        with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
            response = client.get(
                "https://export.arxiv.org/api/query",
                params={"search_query": f"all:{query}", "start": 0, "max_results": limit},
            )
            response.raise_for_status()
        root = ET.fromstring(response.text)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        papers: list[dict[str, str]] = []
        for entry in root.findall("atom:entry", namespace):
            title = " ".join((entry.findtext("atom:title", default="", namespaces=namespace) or "").split())
            summary = " ".join((entry.findtext("atom:summary", default="", namespaces=namespace) or "").split())
            link = entry.findtext("atom:id", default="", namespaces=namespace) or ""
            published = entry.findtext("atom:published", default="", namespaces=namespace) or ""
            papers.append({"title": title, "summary": summary, "url": link, "published": published})
        return papers
