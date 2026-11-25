import json

import httpx

from tests.conftest import NO_AUTH


def test_gemini_test_requires_admin(client, staff_headers):
    assert client.post("/gemini/test", json={}, headers=NO_AUTH).status_code == 401
    assert client.post("/gemini/test", json={}, headers=staff_headers).status_code == 403


def test_gemini_test_requires_api_key(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/gemini/test", json={})
    assert response.status_code == 503
    assert response.json()["detail"] == "GEMINI_API_KEY is not configured"


def test_gemini_test_returns_generated_text(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "unit-test-key")
    original_client = httpx.AsyncClient

    def handler(request):
        assert request.url.path.endswith("/models/gemini-3.6-flash:generateContent")
        assert request.headers["x-goog-api-key"] == "unit-test-key"
        request_body = json.loads(request.content)
        assert request_body["contents"][0]["parts"][0]["text"] == "Say hello"
        assert request_body["generationConfig"]["maxOutputTokens"] == 128
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]},
        )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda timeout: original_client(transport=httpx.MockTransport(handler), timeout=timeout),
    )
    response = client.post("/gemini/test", json={"prompt": "Say hello"})
    assert response.status_code == 200
    assert response.json() == {
        "model": "gemini-3.6-flash",
        "response": "Hello from Gemini",
    }


def test_gemini_chat_requires_admin(client, staff_headers):
    body = {"messages": [{"role": "user", "text": "Test message"}]}
    assert client.post("/gemini/chat", json=body, headers=NO_AUTH).status_code == 401
    assert client.post("/gemini/chat", json=body, headers=staff_headers).status_code == 403


def test_gemini_chat_preserves_turns_and_returns_reply(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "unit-test-key")
    original_client = httpx.AsyncClient

    def handler(request):
        body = json.loads(request.content)
        assert body["contents"] == [
            {"role": "user", "parts": [{"text": "Hi"}]},
            {"role": "model", "parts": [{"text": "Hello"}]},
            {"role": "user", "parts": [{"text": "Say goodbye"}]},
        ]
        assert body["generationConfig"]["maxOutputTokens"] == 512
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "Goodbye"}]}}]},
        )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda timeout: original_client(transport=httpx.MockTransport(handler), timeout=timeout),
    )
    response = client.post("/gemini/chat", json={
        "messages": [
            {"role": "user", "text": "Hi"},
            {"role": "model", "text": "Hello"},
            {"role": "user", "text": "Say goodbye"},
        ],
    })
    assert response.status_code == 200
    assert response.json() == {"model": "gemini-3.6-flash", "response": "Goodbye"}


def test_gemini_chat_rejects_non_alternating_messages(client):
    response = client.post("/gemini/chat", json={
        "messages": [
            {"role": "user", "text": "First"},
            {"role": "user", "text": "Second"},
        ],
    })
    assert response.status_code == 422
