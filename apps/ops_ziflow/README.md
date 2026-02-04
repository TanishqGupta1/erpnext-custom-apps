# OPS ZiFlow App

ZiFlow proofing integration for the OPS ecosystem on Frappe/ERPNext. This app encapsulates the workflows defined in `temp/ziflow_integration_plan.md`: proof creation from OPS Orders, reviewer management, status sync via webhooks/polling, and proof state visibility on OPS doctypes.

## Capabilities
- Creates and maintains `OPS ZiFlow Proof` records mapped to OPS Order Products.
- Adds ZiFlow proofing fields to OPS Order/Product/Customer doctypes.
- Provides whitelisted APIs for proof creation, bulk creation, webhook handling, status sync, and proof summary rendering.
- Includes scheduler fallback for polling ZiFlow when webhooks are unavailable.

## Configuration
Set credentials in site config or environment variables (used via `frappe.conf` fallbacks):
- `ZIFLOW_API_KEY` (required)
- `ZIFLOW_BASE_URL` (default: `https://api.ziflow.com/v1`)
- `ZIFLOW_DEFAULT_FOLDER_ID` (optional)
- `ZIFLOW_DEFAULT_TEMPLATE_ID` (optional)
- `ZIFLOW_DEADLINE_BUFFER_DAYS` (optional, default: `2`)
- `ZIFLOW_WEBHOOK_URL` (optional override; defaults to frappe API endpoint)

## Installation (bench)
1. `bench get-app ops_ziflow .` (or copy this repo into `apps/ops_ziflow`)
2. `bench --site <site> install-app ops_ziflow`
3. Set the config keys above in `site_config.json` and reload: `bench --site <site> reload-doc ops_ziflow`

## Automation
- Proof creation triggers when `OPS Order.order_status` changes to `In Design` or `Order Review`.
- Linked `OPS Order Product` rows are skipped if a `ZiFlow Proof` already exists or the associated `OPS Product.requires_proof_approval` is `0`.
- Webhook handler: `https://<site>/api/method/ops_ziflow.api.ziflow_webhook`
- Polling fallback runs every 5 minutes (`cron` scheduler) for proofs in Draft/In Review/Changes Requested.

## Whitelisted APIs
- `ops_ziflow.api.create_ziflow_proof(ops_order_product)`
- `ops_ziflow.api.bulk_create_proofs(ops_order)`
- `ops_ziflow.api.sync_proof_status(ziflow_proof_id)`
- `ops_ziflow.api.get_proof_summary(ops_order)`
- `ops_ziflow.api.ziflow_webhook()` (guest)

## Webhook registration
`bench --site <site> console` then:
```python
from ops_ziflow.setup.bootstrap import register_webhook
register_webhook()
```

## Notes
- Webhook registration is provided but not auto-run; call `ops_ziflow.setup.bootstrap.register_webhook()` after credentials are set.
- No secrets are hard-coded; all external calls read from config/env.
