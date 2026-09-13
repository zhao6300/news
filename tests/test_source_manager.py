from __future__ import annotations

import pytest

from connectors import RssSourceRegistration, RuntimeSourceManager
from scaffold import CategoryGroup
from searchers import InMemorySearchEngine
from services import InMemoryPlatformService
from storage import InMemoryRepositoryLayer

from tests.test_rss_connector import RSS_XML


def test_runtime_source_manager_adds_rss_to_repository():
    repository = InMemoryRepositoryLayer()
    service = InMemoryPlatformService(())
    search_engine = InMemorySearchEngine([])
    reports = []
    source_manager = RuntimeSourceManager(
        repository,
        service,
        search_engine,
        reports,
        fetcher=lambda feed_url, timeout: RSS_XML,
    )
    payload = {
        "label": "模型研究",
        "category": "models",
        "feed_url": "https://example.com/research.xml",
        "limit": 1,
        "timeout": 5,
    }

    registration = RssSourceRegistration.parse(payload)
    result = source_manager.add_source(payload)

    assert registration.label == "模型研究"
    assert registration.category_id is CategoryGroup.MODELS
    assert registration.limit == 1
    assert registration.timeout == 5
    assert registration.feed_url == "https://example.com/research.xml"
    assert result.article_count == 1
    assert result.report.succeeded is True
    assert repository.total == 1
    assert len(service.extensions) == 1
    assert search_engine.articles[0].source == "模型研究"
    with pytest.raises(ValueError, match="来源标识已存在"):
        source_manager.add_source(payload)

    assert repository.total == 1
    assert len(service.extensions) == 1
    assert len(search_engine.articles) == 1


def test_invalid_rss_source_rejects_input_without_committing_repository_change():
    repository = InMemoryRepositoryLayer()
    service = InMemoryPlatformService(())
    search_engine = InMemorySearchEngine([])
    reports = []
    source_manager = RuntimeSourceManager(
        repository,
        service,
        search_engine,
        reports,
        fetcher=lambda feed_url, timeout: RSS_XML,
    )

    with pytest.raises(ValueError):
        source_manager.add_source(
            {
                "label": "",
                "category": "models",
                "feed_url": "https://example.com/research.xml",
            }
        )

    assert repository.total == 0
    assert len(service.extensions) == 0


def test_duplicate_registration_is_rejected_after_initial_success():
    repository = InMemoryRepositoryLayer()
    service = InMemoryPlatformService(())
    search_engine = InMemorySearchEngine([])
    reports = []
    source_manager = RuntimeSourceManager(
        repository,
        service,
        search_engine,
        reports,
        fetcher=lambda feed_url, timeout: RSS_XML,
    )
    payload = {
        "label": "模型研究",
        "category": "models",
        "feed_url": "https://example.com/research.xml",
    }
    source_manager.add_source(payload)

    with pytest.raises(ValueError, match="来源标识已存在"):
        source_manager.add_source(payload)

    assert repository.total == 1
    assert len(service.extensions) == 1
    assert len(search_engine.articles) == 1
