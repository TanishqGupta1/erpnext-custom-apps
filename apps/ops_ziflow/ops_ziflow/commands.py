"""Bench commands for the OPS ZiFlow app."""

from __future__ import annotations

import json

import click
import frappe
from frappe.commands import pass_context

from ops_ziflow.services.import_service import sync_all_proofs


@click.command("sync-proofs")
@click.option("--folder-id", help="Optional ZiFlow folder id to limit the import")
@click.option("--include-comments", is_flag=True, default=False, help="Also fetch comments for each proof")
@click.option("--page-size", default=50, show_default=True, help="ZiFlow page size")
@click.option("--max-pages", default=20, show_default=True, help="Max pages to fetch")
@pass_context
def sync_proofs(ctx, folder_id: str | None, include_comments: bool, page_size: int, max_pages: int):
    """Backfill ZiFlow proofs into Frappe (idempotent)."""
    res = sync_all_proofs(
        page_size=page_size,
        max_pages=max_pages,
        folder_id=folder_id,
        include_comments=include_comments,
    )
    click.echo(json.dumps(res, indent=2))


commands = [sync_proofs]
