from fastapi import FastAPI, Query
from opensearchpy import AsyncOpenSearch
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Search Service", version="1.0.0")

# OpenSearch client
opensearch_client = AsyncOpenSearch(
    hosts=[{"host": os.getenv("OPENSEARCH_ENDPOINT", "localhost"), "port": 443}],
    http_auth=(os.getenv("OPENSEARCH_USER", "admin"), os.getenv("OPENSEARCH_PASSWORD", "")),
    use_ssl=True,
    verify_certs=True,
)

@app.get("/search/events")
async def search_events(
    q: str = Query(..., min_length=1),
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100)
):
    """이벤트 검색"""
    must_clauses = [{"multi_match": {"query": q, "fields": ["title^3", "description^2", "venue"]}}]
    filter_clauses = [{"term": {"status": "published"}}]

    if category:
        filter_clauses.append({"term": {"category": category}})
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price: price_range["gte"] = min_price
        if max_price: price_range["lte"] = max_price
        filter_clauses.append({"range": {"price": price_range}})

    try:
        response = await opensearch_client.search(
            index="events",
            body={
                "query": {"bool": {"must": must_clauses, "filter": filter_clauses}},
                "from": (page - 1) * size,
                "size": size,
                "sort": [{"is_featured": {"order": "desc"}}, {"start_time": {"order": "asc"}}]
            }
        )

        return {
            "events": [hit["_source"] for hit in response["hits"]["hits"]],
            "total": response["hits"]["total"]["value"],
            "page": page,
            "size": size
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"events": [], "total": 0}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "search-service", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {"service": "Search Service", "version": "1.0.0"}
