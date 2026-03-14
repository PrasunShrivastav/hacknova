"""PubMed search tool via NCBI E-utilities — free, optional API key for higher rate limits."""

import httpx
import os
import time
import logging
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# With API key: 10 req/sec. Without: 3 req/sec.
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")


def search_pubmed(query: str, max_results: int = 10) -> list[dict]:
    """Search PubMed for biomedical papers using NCBI E-utilities.

    Free tier: 3 requests/second without an API key.

    Args:
        query: Search query string.
        max_results: Maximum papers to return.

    Returns:
        List of paper dicts with title, abstract, year, source.
    """
    logger.info(f"Searching PubMed for: '{query}' (max {max_results})")

    # Step 1: Get PubMed IDs
    try:
        search_resp = httpx.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                **(({"api_key": NCBI_API_KEY}) if NCBI_API_KEY else {}),
            },
            timeout=30,
        )
        search_resp.raise_for_status()
        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.error(f"PubMed search error: {e}")
        return []

    if not ids:
        logger.info("PubMed returned 0 results")
        return []

    time.sleep(0.4)  # Respect 3 req/sec limit

    # Step 2: Fetch full records as XML
    try:
        fetch_resp = httpx.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "xml",
                "rettype": "abstract",
                **(({"api_key": NCBI_API_KEY}) if NCBI_API_KEY else {}),
            },
            timeout=30,
        )
        fetch_resp.raise_for_status()
    except Exception as e:
        logger.error(f"PubMed fetch error: {e}")
        return []

    # Step 3: Parse XML
    papers = []
    try:
        root = ET.fromstring(fetch_resp.text)
        for article in root.findall(".//PubmedArticle"):
            title_el = article.find(".//ArticleTitle")
            year_el = article.find(".//PubDate/Year")
            pmid_el = article.find(".//PMID")

            # Concatenate all AbstractText sections (some papers have structured abstracts)
            abstract_parts = []
            for abs_el in article.findall(".//AbstractText"):
                label = abs_el.get("Label", "")
                text = abs_el.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # Collect authors
            authors = []
            for author_el in article.findall(".//Author"):
                last = author_el.findtext("LastName", "")
                first = author_el.findtext("ForeName", "")
                if last:
                    authors.append(f"{first} {last}".strip())

            pmid = pmid_el.text if pmid_el is not None else ""

            papers.append({
                "title": title_el.text if title_el is not None else "",
                "abstract": abstract,
                "authors": authors,
                "year": int(year_el.text) if year_el is not None and year_el.text else None,
                "paper_id": f"pmid:{pmid}" if pmid else "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "source": "pubmed",
            })
    except ET.ParseError as e:
        logger.error(f"PubMed XML parse error: {e}")

    logger.info(f"PubMed returned {len(papers)} papers")
    return papers
