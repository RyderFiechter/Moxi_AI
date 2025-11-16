"""Shared HTTP client helpers for interacting with the storage node API."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
import urllib.error
import urllib.request

DEFAULT_API_BASE = "http://localhost:8000"
API_ENVVAR = "MOXI_NODE_API"


class NodeAPIError(RuntimeError):
    """Raised when HTTP calls to the node API fail."""


def _build_url(base: str, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return base.rstrip("/") + path


def _extract_error_message(body: str, fallback: str) -> str:
    if not body:
        return fallback
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body.strip() or fallback
    return (
        data.get("detail")
        or data.get("error")
        or data.get("message")
        or body.strip()
        or fallback
    )


class NodeAPIClient:
    """Lightweight HTTP client for the storage node API."""

    def __init__(
        self,
        base_url: str = DEFAULT_API_BASE,
        timeout: float = 10.0,
        *,
        api_base: Optional[str] = None,
    ) -> None:
        # Support both base_url and api_base keyword names
        self.base_url = api_base or base_url
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = _build_url(self.base_url, path)
        headers = {"Accept": "application/json"}
        data_bytes = None

        if payload is not None:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=data_bytes,
            method=method,
            headers=headers,
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8").strip()
                if not body:
                    return None
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            detail = _extract_error_message(
                exc.read().decode("utf-8", errors="ignore"), str(exc)
            )
            raise NodeAPIError(f"{method} {url} failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise NodeAPIError(f"Unable to reach node API at {url}: {exc.reason}") from exc

    # Convenience wrappers -------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        return self.request("GET", "/status")

    def get_config(self) -> Dict[str, Any]:
        return self.request("GET", "/config")

    def get_registry_status(self) -> Dict[str, Any]:
        return self.request("GET", "/registry/status")

    def update_payment_wallet(self, wallet: str) -> Dict[str, Any]:
        return self.request(
            "PUT", "/payment-wallet", payload={"payment_wallet": wallet}
        )

    def set_storage_lending(self, enabled: bool) -> Dict[str, Any]:
        return self.request(
            "POST", f"/storage-lending/{'enable' if enabled else 'disable'}"
        )

    def register_storage(self, storage_gb: int, price_per_gb_eth: float) -> Dict[str, Any]:
        return self.request(
            "POST",
            "/registry/register",
            payload={"storage_gb": storage_gb, "price_per_gb_eth": price_per_gb_eth},
        )

    def update_registry_storage(self) -> Dict[str, Any]:
        return self.request("POST", "/registry/update")

    def activate_registry(self) -> Dict[str, Any]:
        return self.request("POST", "/registry/activate")

    def deactivate_registry(self) -> Dict[str, Any]:
        return self.request("POST", "/registry/deactivate")

    def send_payout(self) -> Dict[str, Any]:
        return self.request("POST", "/payout")
