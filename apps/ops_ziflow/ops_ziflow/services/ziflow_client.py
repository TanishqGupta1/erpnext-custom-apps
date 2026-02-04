"""Thin ZiFlow HTTP client with retries and structured errors."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ops_ziflow.utils.config import ZiFlowSettings
from ops_ziflow.utils.errors import ZiFlowError

LOGGER = logging.getLogger(__name__)


class ZiFlowClient:
    def __init__(self, settings: ZiFlowSettings):
        if not settings.api_key:
            raise ZiFlowError("ZIFLOW_API_KEY is missing")
        self.settings = settings
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({"apikey": settings.api_key, "Content-Type": "application/json"})

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.settings.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.request(method, url, timeout=30, **kwargs)
        except requests.RequestException as exc:
            raise ZiFlowError(f"ZiFlow network error: {exc}") from exc

        if resp.status_code >= 400:
            message = self._extract_error(resp)
            raise ZiFlowError(message, status_code=resp.status_code)

        if not resp.text:
            return {}
        try:
            return resp.json()
        except ValueError:
            LOGGER.warning("Non-JSON response from ZiFlow at %s", url)
            return {"raw": resp.text}

    @staticmethod
    def _extract_error(resp: requests.Response) -> str:
        try:
            parsed = resp.json()
            return parsed.get("message") or parsed.get("error") or resp.text
        except Exception:
            return resp.text

    # API operations -----------------------------------------------------
    def create_proof(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "proofs", json=payload)

    def get_proof(self, proof_id: str) -> Dict[str, Any]:
        return self._request("GET", f"proofs/{proof_id}")

    def list_proofs(self, page: int = 1, page_size: int = 50, folder_id: str | None = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if folder_id:
            params["folder_id"] = folder_id
        return self._request("GET", "proofs", params=params)

    def create_version(self, proof_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"proofs/{proof_id}/versions", json=payload)

    def get_comments(self, proof_id: str) -> Dict[str, Any]:
        return self._request("GET", f"proofs/{proof_id}/comments")

    def list_folders(self, page: int = 1, page_size: int = 100, parent_id: str | None = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if parent_id:
            params["parent_id"] = parent_id
        return self._request("GET", "folders", params=params)

    def get_folder(self, folder_id: str) -> Dict[str, Any]:
        return self._request("GET", f"folders/{folder_id}")

    def add_reviewer(self, proof_id: str, reviewer: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"proofs/{proof_id}/reviewers", json=reviewer)

    def create_webhook(self, url: str, events: list[str]) -> Dict[str, Any]:
        return self._request("POST", "webhooks", json={"url": url, "events": events})

    def submit_review(self, proof_id: str, decision: str, message: str | None = None) -> Dict[str, Any]:
        payload = {"decision": decision}
        if message:
            payload["message"] = message
        return self._request("POST", f"proofs/{proof_id}/decision", json=payload)
