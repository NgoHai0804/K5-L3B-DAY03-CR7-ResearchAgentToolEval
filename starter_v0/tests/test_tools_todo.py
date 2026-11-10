"""Tool unit tests (challenge done: 0 skipped).

Patterns come from test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send = TOOL_FUNCTIONS["send"]
lookup = TOOL_FUNCTIONS["lookup"]
fetch = TOOL_FUNCTIONS["fetch"]
timeline = TOOL_FUNCTIONS["timeline"]
social_search = TOOL_FUNCTIONS["social_search"]
policy = TOOL_FUNCTIONS["policy"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify(question="Bạn muốn nguồn nào?", response_type="choice", options=["Web", "Twitter"])

    assert result["options"] == ["Web", "Twitter"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]

    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("a2") < markdown.index("## B")  # a2 grouped under A, not after B


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"tin {i}", "url": f"https://x.com/{i}"} for i in range(3)]
    lines = format_tool(items=items, template="thread")["markdown"].split("\n\n")

    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]


@pytest.mark.parametrize("items", [None, []])
def test_format_empty_items_does_not_crash(items) -> None:
    result = format_tool(items=items, template="sections")
    assert result["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@channel")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "bot-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "@channel"
    assert calls[0]["json"]["text"] == "Bản tin"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    lookup(query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Body",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/post"},
    }}))

    result = fetch(url="https://www.example.com/post")

    assert calls[0]["json"]["url"] == "https://www.example.com/post"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.example.com/post", "source": "example.com", "summary": "# Body",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    summary = fetch(url="https://example.com")["items"][0]["summary"]

    assert len(summary) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    raw = [{"text": "no id", "screen_name": "sama"}] + [
        {"tweet_id": str(i), "text": f"tweet {i}", "screen_name": "sama"} for i in range(6)
    ]
    calls = fake_http(FakeResponse({"timeline": raw}))

    items = timeline(screenname="sama", limit=3)["items"]

    assert calls[0]["params"] == {"screenname": "sama"}
    assert [item["url"] for item in items] == [f"https://x.com/sama/status/{i}" for i in range(3)]


@pytest.mark.parametrize("search_type", ["Top", "Latest"])
def test_social_search_passes_search_type(monkeypatch, fake_http, search_type) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"timeline": []}))

    result = social_search(query="OpenAI", search_type=search_type)

    assert calls[0]["params"] == {"query": "OpenAI", "search_type": search_type}
    assert result["search_type"] == search_type


# ---------------- policy (local knowledge + trust boundary) ----------------

@pytest.mark.parametrize("query", ["", "   ", "và là của"])  # only stopwords -> no search terms
def test_policy_empty_query_returns_no_results(query) -> None:
    assert policy(query=query)["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    results = policy(query="dữ liệu khách hàng API key", policy_area="data_privacy", top_k=5)["results"]

    assert results
    assert {result["policy_area"] for result in results} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # source-citation-policy.md has an "Injection probe" section: a quoted line that
    # tries to give the assistant orders. It must never be returned as a fact.
    results = policy(query="injection probe citation", policy_area="source_citation", top_k=5)["results"]
    probe = next(result for result in results if result["section"] == "Injection probe")

    assert any("viral tweet" in line for line in probe["untrusted_text"])
    assert "viral tweet" not in probe["facts"]
    assert all("ignore" not in result["facts"].lower() for result in results)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

rank_items = TOOL_FUNCTIONS["rank_items"]
wiki = TOOL_FUNCTIONS["wiki"]


# ---- rank_items (local, offline: no mock needed) ----

def _titles(result: dict) -> list[str]:
    return [item["title"] for item in result["items"]]


# 1. happy path

def test_rank_items_dedupes_by_url_and_reports_removed() -> None:
    items = [
        {"title": "A", "url": "https://x.com/a"},
        {"title": "A again", "url": "https://x.com/a"},
        {"title": "B", "url": "https://x.com/b"},
    ]
    result = rank_items(items=items)

    assert _titles(result) == ["A", "B"]
    assert result["count"] == 2
    assert result["removed"] == 1


def test_rank_items_score_sorts_desc_and_falls_back_to_points() -> None:
    # Sources name popularity differently (`points`, `score`): both must rank together.
    items = [
        {"title": "low", "url": "https://1", "score": 1},
        {"title": "hn-hot", "url": "https://2", "points": 500},
        {"title": "mid", "url": "https://3", "score": 7},
    ]
    result = rank_items(items=items, sort_by="score")
    assert _titles(result) == ["hn-hot", "mid", "low"]


def test_rank_items_recency_sorts_newest_first() -> None:
    items = [
        {"title": "old", "url": "https://1", "date": "2026-01-01"},
        {"title": "new", "url": "https://2", "date": "2026-06-01"},
        {"title": "mid", "url": "https://3", "published": "2026-03-01"},
    ]
    result = rank_items(items=items, sort_by="recency")
    assert _titles(result) == ["new", "mid", "old"]


def test_rank_items_relevance_puts_keyword_match_first() -> None:
    items = [
        {"title": "Rust async runtime", "url": "https://1"},
        {"title": "Diffusion models for video", "url": "https://2"},
    ]
    result = rank_items(items=items, sort_by="relevance", query="diffusion")
    assert _titles(result)[0] == "Diffusion models for video"


def test_rank_items_top_k_limits_output() -> None:
    items = [{"title": str(i), "url": f"https://{i}"} for i in range(5)]
    result = rank_items(items=items, top_k=2)
    assert result["count"] == 2


# 2. bad input from the model (regression tests for the PLAN-v3 skeleton bugs)

def test_rank_items_top_k_as_string_is_coerced() -> None:
    items = [{"title": str(i), "url": f"https://{i}"} for i in range(5)]
    assert rank_items(items=items, top_k="2")["count"] == 2  # skeleton: silently 10


def test_rank_items_top_k_bool_falls_back_to_default() -> None:
    items = [{"title": str(i), "url": f"https://{i}"} for i in range(5)]
    assert rank_items(items=items, top_k=True)["count"] == 5  # skeleton: True == 1


def test_rank_items_non_numeric_score_does_not_crash() -> None:
    items = [
        {"title": "bad", "url": "https://1", "score": "abc"},
        {"title": "good", "url": "https://2", "score": 3},
    ]
    result = rank_items(items=items, sort_by="score")  # skeleton: ValueError
    assert _titles(result) == ["good", "bad"]


def test_rank_items_trailing_slash_url_counts_as_duplicate() -> None:
    items = [{"title": "A", "url": "https://x.com/a/"}, {"title": "A", "url": "https://x.com/a"}]
    result = rank_items(items=items)
    assert result["count"] == 1
    assert result["removed"] == 1


def test_rank_items_skips_non_dict_items() -> None:
    result = rank_items(items=[{"title": "ok", "url": "https://1"}, "junk", None, 42])
    assert _titles(result) == ["ok"]
    assert result["removed"] == 3


def test_rank_items_empty_list_returns_zero() -> None:
    result = rank_items(items=[])
    assert (result["items"], result["count"], result["removed"]) == ([], 0, 0)


# 3. failure path -> error dict, never raise

def test_rank_items_non_list_items_returns_error_dict() -> None:
    result = rank_items(items="not-a-list")
    assert result["tool"] == "rank_items"
    assert result["error"] == "ValueError"
    assert "items" not in result


def test_rank_items_unknown_sort_by_returns_error_dict() -> None:
    result = rank_items(items=[], sort_by="popularity")
    assert result["error"] == "ValueError"
    assert "popularity" in result["message"]


def test_rank_items_relevance_without_query_returns_error_dict() -> None:
    result = rank_items(items=[{"title": "x", "url": "https://1"}], sort_by="relevance")
    assert result["error"] == "ValueError"
    assert "query" in result["message"]


# ---- wiki (live API: always mock HTTP with fake_http) ----

WIKI_PAGE = {
    "pageid": 61603971,
    "title": "Transformer (deep learning)",
    "fullurl": "https://en.wikipedia.org/wiki/Transformer_(deep_learning)",
    "extract": "In deep learning, the transformer is a family of neural network architectures.\n",
}


def _wiki_payload(*pages: dict) -> dict:
    return {"batchcomplete": True, "query": {"pages": list(pages)}} if pages else {"batchcomplete": True}


# 1. happy path: assert the request we send AND how we map the response

def test_wiki_sends_one_search_plus_extract_request(fake_http) -> None:
    calls = fake_http(FakeResponse(_wiki_payload(WIKI_PAGE)))

    wiki(query="transformer deep learning", sentences=3)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://en.wikipedia.org/w/api.php"
    params = calls[0]["params"]
    assert (params["generator"], params["gsrsearch"], params["gsrlimit"]) == ("search", "transformer deep learning", 1)
    assert params["exsentences"] == 3
    assert "User-Agent" in calls[0]["headers"]


def test_wiki_maps_page_to_item(fake_http) -> None:
    fake_http(FakeResponse(_wiki_payload(WIKI_PAGE)))

    result = wiki(query="transformer")

    assert result["found"] is True
    assert result["items"] == [{
        "title": "Transformer (deep learning)",
        "url": "https://en.wikipedia.org/wiki/Transformer_(deep_learning)",
        "source": "en.wikipedia.org",
        "summary": "In deep learning, the transformer is a family of neural network architectures.",
        "is_disambiguation": False,
    }]


def test_wiki_lang_vi_calls_vietnamese_wikipedia(fake_http) -> None:
    calls = fake_http(FakeResponse(_wiki_payload(WIKI_PAGE)))
    result = wiki(query="trí tuệ nhân tạo", lang="vi")
    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert result["items"][0]["source"] == "vi.wikipedia.org"


def test_wiki_flags_disambiguation_page(fake_http) -> None:
    page = {"title": "Mercury", "fullurl": "https://en.wikipedia.org/wiki/Mercury",
            "extract": "Mercury most commonly refers to:", "pageprops": {"disambiguation": ""}}
    fake_http(FakeResponse(_wiki_payload(page)))
    assert wiki(query="Mercury")["items"][0]["is_disambiguation"] is True


def test_wiki_no_match_returns_found_false(fake_http) -> None:
    fake_http(FakeResponse(_wiki_payload()))
    result = wiki(query="zzqqxxnonexistent123")
    assert (result["found"], result["items"]) == (False, [])
    assert "error" not in result


# 2. bad input from the model

@pytest.mark.parametrize("query", ["", "   ", None, ["transformer"]])
def test_wiki_empty_or_non_string_query_returns_error_and_no_request(fake_http, query) -> None:
    calls = fake_http(FakeResponse(_wiki_payload(WIKI_PAGE)))
    result = wiki(query=query)
    assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_unsupported_lang_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse(_wiki_payload(WIKI_PAGE)))
    result = wiki(query="transformer", lang="fr")
    assert result["error"] == "ValueError"
    assert calls == []


@pytest.mark.parametrize(("sentences", "sent"), [("4", 4), (0, 1), (99, 10), (True, 5), ("abc", 5)])
def test_wiki_sentences_is_coerced_and_clamped(fake_http, sentences, sent) -> None:
    calls = fake_http(FakeResponse(_wiki_payload(WIKI_PAGE)))
    wiki(query="transformer", sentences=sentences)
    assert calls[0]["params"]["exsentences"] == sent


# 3. failure path -> error dict, never raise

def test_wiki_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    result = wiki(query="transformer")
    assert result["tool"] == "wiki_summary"
    assert result["error"] == "HTTPError"


def test_wiki_network_timeout_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("read timed out"))
    assert wiki(query="transformer")["error"] == "Timeout"


# ---- github_repo (live API: always mock HTTP with fake_http) ----

github_repo = TOOL_FUNCTIONS["github_repo"]

GH_REPO = {
    "full_name": "langchain-ai/langchain",
    "name": "langchain",
    "html_url": "https://github.com/langchain-ai/langchain",
    "description": "The agent engineering platform.",
    "stargazers_count": 149300,
    "forks_count": 25103,
    "open_issues_count": 739,
    "language": "Python",
    "license": {"spdx_id": "MIT"},
    "topics": ["llm", "agents"],
    "pushed_at": "2026-11-10T08:28:09Z",
    "archived": False,
}


# 1. happy path

def test_github_repo_owner_name_calls_repos_endpoint_and_maps_fields(fake_http) -> None:
    calls = fake_http(FakeResponse(GH_REPO))

    result = github_repo(repo="langchain-ai/langchain")

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.github.com/repos/langchain-ai/langchain"
    assert result["found"] is True
    assert result["items"] == [{
        "title": "langchain-ai/langchain",
        "url": "https://github.com/langchain-ai/langchain",
        "source": "github.com",
        "summary": "The agent engineering platform.",
        "stars": 149300,
        "forks": 25103,
        "open_issues": 739,
        "language": "Python",
        "license": "MIT",
        "topics": ["llm", "agents"],
        "last_push": "2026-11-10T08:28:09Z",
        "archived": False,
    }]


@pytest.mark.parametrize("repo", [
    "https://github.com/langchain-ai/langchain",
    "github.com/langchain-ai/langchain.git",
    "  langchain-ai/langchain/  ",
])
def test_github_repo_normalizes_urls_to_owner_name(fake_http, repo) -> None:
    calls = fake_http(FakeResponse(GH_REPO))
    github_repo(repo=repo)
    assert calls[0]["url"] == "https://api.github.com/repos/langchain-ai/langchain"


def test_github_repo_bare_name_searches_and_prefers_exact_name(fake_http) -> None:
    # Regression: sorting by stars returned a huge unrelated repo first.
    other = dict(GH_REPO, full_name="microsoft/markitdown", name="markitdown", stargazers_count=194000)
    calls = fake_http(FakeResponse({"items": [other, GH_REPO]}))

    result = github_repo(repo="langchain")

    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"]["q"] == "langchain in:name"
    assert "sort" not in calls[0]["params"]
    assert result["repo"] == "langchain-ai/langchain"


def test_github_repo_sends_token_only_when_set(monkeypatch, fake_http) -> None:
    calls = fake_http(FakeResponse(GH_REPO))
    github_repo(repo="a/b")
    monkeypatch.setenv("GITHUB_TOKEN", "gh-test")
    github_repo(repo="a/b")

    assert "Authorization" not in calls[0]["headers"]
    assert calls[1]["headers"]["Authorization"] == "Bearer gh-test"


# 2. bad input from the model

@pytest.mark.parametrize("repo", ["", "   ", None, 123])
def test_github_repo_empty_or_non_string_returns_error_and_no_request(fake_http, repo) -> None:
    calls = fake_http(FakeResponse(GH_REPO))
    result = github_repo(repo=repo)
    assert result["error"] == "ValueError"
    assert calls == []


# 3. failure path -> error dict / found=false, never raise

def test_github_repo_404_returns_found_false(fake_http) -> None:
    fake_http(FakeResponse({"message": "Not Found"}, status_code=404))
    result = github_repo(repo="nope/none")
    assert (result["found"], result["items"]) == (False, [])
    assert "error" not in result


def test_github_repo_search_without_match_returns_found_false(fake_http) -> None:
    fake_http(FakeResponse({"items": []}))
    assert github_repo(repo="zzqqxx")["found"] is False


def test_github_repo_rate_limit_returns_actionable_error(fake_http) -> None:
    limited = FakeResponse({"message": "API rate limit exceeded"}, status_code=403)
    limited.headers = {"x-ratelimit-remaining": "0"}
    fake_http(limited)

    result = github_repo(repo="a/b")

    assert result["error"] == "RuntimeError"
    assert "GITHUB_TOKEN" in result["message"]


def test_github_repo_server_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    assert github_repo(repo="a/b")["error"] == "HTTPError"


def test_github_repo_timeout_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("read timed out"))
    assert github_repo(repo="a/b")["error"] == "Timeout"


# ---- hf_models (live API: always mock HTTP with fake_http) ----

hf_models = TOOL_FUNCTIONS["hf_models"]

HF_MODEL = {
    "id": "Qwen/Qwen3-0.6B",
    "pipeline_tag": "text-generation",
    "library_name": "transformers",
    "downloads": 20511631,
    "likes": 1889,
    "tags": ["transformers", "license:apache-2.0", "arxiv:2505.09388", "text-generation"],
    "createdAt": "2025-04-27T03:40:08.000Z",
}


# 1. happy path

def test_hf_models_search_sends_expected_request_and_maps_model(fake_http) -> None:
    calls = fake_http(FakeResponse([HF_MODEL]))

    result = hf_models(query="qwen", limit=3)

    assert calls[0]["url"] == "https://huggingface.co/api/models"
    assert calls[0]["params"] == {"search": "qwen", "sort": "downloads", "direction": -1, "limit": 3}
    assert result["items"] == [{
        "title": "Qwen/Qwen3-0.6B",
        "url": "https://huggingface.co/Qwen/Qwen3-0.6B",
        "source": "huggingface.co",
        "task": "text-generation",
        "library": "transformers",
        "downloads": 20511631,
        "likes": 1889,
        "license": "apache-2.0",
        "arxiv": ["2505.09388"],
        "gated": False,
        "date": "2025-04-27T03:40:08.000Z",
    }]


@pytest.mark.parametrize(("sort_by", "param"), [("downloads", "downloads"), ("likes", "likes"),
                                                ("trending", "trendingScore"), ("recent", "createdAt")])
def test_hf_models_sort_by_maps_to_hub_param(fake_http, sort_by, param) -> None:
    calls = fake_http(FakeResponse([]))
    hf_models(query="llama", sort_by=sort_by)
    assert calls[0]["params"]["sort"] == param


def test_hf_models_task_only_filters_by_pipeline_tag(fake_http) -> None:
    calls = fake_http(FakeResponse([HF_MODEL]))
    hf_models(task="automatic-speech-recognition")
    assert calls[0]["params"]["pipeline_tag"] == "automatic-speech-recognition"
    assert "search" not in calls[0]["params"]


def test_hf_models_model_id_calls_detail_endpoint(fake_http) -> None:
    detail = dict(HF_MODEL, gated="manual", lastModified="2026-01-01T00:00:00.000Z")
    calls = fake_http(FakeResponse(detail))

    result = hf_models(model_id="Qwen/Qwen3-0.6B")

    assert calls[0]["url"] == "https://huggingface.co/api/models/Qwen/Qwen3-0.6B"
    assert result["found"] is True
    assert result["items"][0]["gated"] is True
    assert result["items"][0]["date"] == "2026-01-01T00:00:00.000Z"  # lastModified wins over createdAt


def test_hf_models_model_without_license_tag_has_none(fake_http) -> None:
    fake_http(FakeResponse([dict(HF_MODEL, tags=["transformers"])]))
    item = hf_models(query="x")["items"][0]
    assert (item["license"], item["arxiv"]) == (None, [])


# 2. bad input from the model

def test_hf_models_limit_as_string_is_coerced_and_clamped(fake_http) -> None:
    calls = fake_http(FakeResponse([]))
    hf_models(query="x", limit="7")
    hf_models(query="x", limit=999)
    hf_models(query="x", limit=True)
    assert [call["params"]["limit"] for call in calls] == [7, 20, 5]


def test_hf_models_no_query_no_task_no_id_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse([]))
    result = hf_models()
    assert result["error"] == "ValueError"
    assert calls == []


def test_hf_models_unknown_sort_by_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse([]))
    result = hf_models(query="x", sort_by="popular")
    assert result["error"] == "ValueError"
    assert calls == []


@pytest.mark.parametrize("model_id", ["Qwen3-0.6B", "https://huggingface.co/Qwen/Qwen3", "a/b/c"])
def test_hf_models_malformed_model_id_returns_error_and_no_request(fake_http, model_id) -> None:
    calls = fake_http(FakeResponse(HF_MODEL))
    assert hf_models(model_id=model_id)["error"] == "ValueError"
    assert calls == []


# 3. failure path -> found=false / error dict, never raise

@pytest.mark.parametrize("status", [401, 404])
def test_hf_models_missing_model_returns_found_false(fake_http, status) -> None:
    # The Hub answers 401 (not 404) for a model that does not exist.
    fake_http(FakeResponse({"error": "Repository not found"}, status_code=status))
    result = hf_models(model_id="nope/none")
    assert (result["found"], result["items"]) == (False, [])
    assert "error" not in result


def test_hf_models_server_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert hf_models(query="x")["error"] == "HTTPError"


def test_hf_models_timeout_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("read timed out"))
    assert hf_models(query="x")["error"] == "Timeout"
