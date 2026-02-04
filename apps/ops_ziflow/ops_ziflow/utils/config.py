from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import frappe


def _conf(key: str, default: Any | None = None) -> Any:
    if getattr(frappe, "conf", None):
        value = frappe.conf.get(key)
        if value is not None:
            return value
    return os.getenv(key, default)


@dataclass
class ZiFlowSettings:
    api_key: str | None
    base_url: str
    default_folder_id: str | None
    default_template_id: str | None
    deadline_buffer_days: int
    webhook_url: str | None
    webhook_events: list[str]


def load_settings() -> ZiFlowSettings:
    return ZiFlowSettings(
        api_key=_conf("ZIFLOW_API_KEY"),
        base_url=_conf("ZIFLOW_BASE_URL", "https://api.ziflow.com/v1").rstrip("/"),
        default_folder_id=_conf("ZIFLOW_DEFAULT_FOLDER_ID"),
        default_template_id=_conf("ZIFLOW_DEFAULT_TEMPLATE_ID"),
        deadline_buffer_days=int(_conf("ZIFLOW_DEADLINE_BUFFER_DAYS", 2)),
        webhook_url=_conf("ZIFLOW_WEBHOOK_URL"),
        webhook_events=[
            "proof.approved",
            "proof.rejected",
            "proof.comment_added",
            "proof.version_created",
        ],
    )


def require_api_key(settings: ZiFlowSettings) -> None:
    if not settings.api_key:
        raise frappe.ValidationError("ZiFlow API key is not configured (ZIFLOW_API_KEY).")
