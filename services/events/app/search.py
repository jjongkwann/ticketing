import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from opensearchpy._async.client import AsyncOpenSearch

logger = logging.getLogger(__name__)

# OpenSearch client
opensearch_client = None


def get_opensearch_client() -> AsyncOpenSearch:
    """OpenSearch 클라이언트 가져오기"""
    global opensearch_client

    if opensearch_client is None:
        opensearch_endpoint = os.getenv("OPENSEARCH_ENDPOINT", "")
        opensearch_user = os.getenv("OPENSEARCH_USER", "admin")
        opensearch_password = os.getenv("OPENSEARCH_PASSWORD", "")

        if not opensearch_endpoint:
            logger.warning("OPENSEARCH_ENDPOINT not set, search functionality will be disabled")
            return None

        opensearch_client = AsyncOpenSearch(
            hosts=[{"host": opensearch_endpoint.replace("https://", ""), "port": 443}],
            http_auth=(opensearch_user, opensearch_password),
            use_ssl=True,
            verify_certs=True,
            ssl_show_warn=False,
        )

    return opensearch_client


INDEX_NAME = "events"


async def init_opensearch_index():
    """OpenSearch 인덱스 초기화"""
    client = get_opensearch_client()
    if not client:
        return

    index_body = {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "korean_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop"],
                    }
                }
            },
        },
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "text", "analyzer": "korean_analyzer"},
                "description": {"type": "text", "analyzer": "korean_analyzer"},
                "venue": {"type": "text"},
                "address": {"type": "text"},
                "start_time": {"type": "date"},
                "end_time": {"type": "date"},
                "total_seats": {"type": "integer"},
                "available_seats": {"type": "integer"},
                "price": {"type": "float"},
                "currency": {"type": "keyword"},
                "status": {"type": "keyword"},
                "category": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "is_featured": {"type": "boolean"},
                "organizer_id": {"type": "integer"},
                "created_at": {"type": "date"},
            }
        },
    }

    try:
        exists = await client.indices.exists(index=INDEX_NAME)
        if not exists:
            await client.indices.create(index=INDEX_NAME, body=index_body)
            logger.info(f"Created OpenSearch index: {INDEX_NAME}")
    except Exception as e:
        logger.error(f"Failed to create OpenSearch index: {e}")


async def index_event(event_data: Dict[str, Any]):
    """이벤트를 OpenSearch에 인덱싱"""
    client = get_opensearch_client()
    if not client:
        return

    try:
        # Decimal을 float으로 변환
        if "price" in event_data and isinstance(event_data["price"], Decimal):
            event_data["price"] = float(event_data["price"])

        # datetime을 ISO 문자열로 변환
        for field in ["start_time", "end_time", "created_at", "updated_at"]:
            if field in event_data and isinstance(event_data[field], datetime):
                event_data[field] = event_data[field].isoformat()

        await client.index(
            index=INDEX_NAME,
            id=event_data["id"],
            body=event_data,
            refresh=True,
        )
        logger.info(f"Indexed event {event_data['id']} to OpenSearch")
    except Exception as e:
        logger.error(f"Failed to index event: {e}")


async def update_event_in_index(event_id: int, event_data: Dict[str, Any]):
    """OpenSearch에서 이벤트 업데이트"""
    client = get_opensearch_client()
    if not client:
        return

    try:
        # Decimal/datetime 변환
        if "price" in event_data and isinstance(event_data["price"], Decimal):
            event_data["price"] = float(event_data["price"])

        for field in ["start_time", "end_time", "created_at", "updated_at"]:
            if field in event_data and isinstance(event_data[field], datetime):
                event_data[field] = event_data[field].isoformat()

        await client.update(
            index=INDEX_NAME,
            id=event_id,
            body={"doc": event_data},
            refresh=True,
        )
        logger.info(f"Updated event {event_id} in OpenSearch")
    except Exception as e:
        logger.error(f"Failed to update event in search index: {e}")


async def delete_event_from_index(event_id: int):
    """OpenSearch에서 이벤트 삭제"""
    client = get_opensearch_client()
    if not client:
        return

    try:
        await client.delete(index=INDEX_NAME, id=event_id, refresh=True)
        logger.info(f"Deleted event {event_id} from OpenSearch")
    except Exception as e:
        logger.error(f"Failed to delete event from search index: {e}")


async def search_events(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """이벤트 검색"""
    client = get_opensearch_client()
    if not client:
        return {"events": [], "total": 0}

    # 검색 쿼리 구성
    must_clauses = []

    if query:
        must_clauses.append(
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "description^2", "venue"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        )

    # 필터 조건
    filter_clauses = [{"term": {"status": "published"}}]

    if category:
        filter_clauses.append({"term": {"category": category}})

    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = float(min_price)
        if max_price is not None:
            price_range["lte"] = float(max_price)
        filter_clauses.append({"range": {"price": price_range}})

    if start_date or end_date:
        date_range = {}
        if start_date:
            date_range["gte"] = start_date.isoformat()
        if end_date:
            date_range["lte"] = end_date.isoformat()
        filter_clauses.append({"range": {"start_time": date_range}})

    # 최종 쿼리
    search_query = {
        "bool": {
            "must": must_clauses if must_clauses else [{"match_all": {}}],
            "filter": filter_clauses,
        }
    }

    # 검색 실행
    from_offset = (page - 1) * page_size

    try:
        response = await client.search(
            index=INDEX_NAME,
            body={
                "query": search_query,
                "from": from_offset,
                "size": page_size,
                "sort": [
                    {"is_featured": {"order": "desc"}},
                    {"start_time": {"order": "asc"}},
                    {"_score": {"order": "desc"}},
                ],
            },
        )

        events = [hit["_source"] for hit in response["hits"]["hits"]]
        total = response["hits"]["total"]["value"]

        return {"events": events, "total": total}
    except Exception as e:
        logger.error(f"Failed to search events: {e}")
        return {"events": [], "total": 0}
