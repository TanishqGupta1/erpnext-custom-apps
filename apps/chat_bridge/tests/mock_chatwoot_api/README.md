# Mock Chatwoot API Server

Mock server for testing Chatwoot ERPNext integration without touching production Chatwoot.

## Usage

### Start the server:
```bash
cd E:\Docker\Frappe\apps\chat_bridge\tests\mock_chatwoot_api
pip install -r requirements.txt
python mock_server.py
```

Server runs on `http://localhost:3001`

### From Docker containers:
Use `http://host.docker.internal:3001` to access from ERPNext containers.

## Endpoints

All Chatwoot API endpoints are mocked:
- `/api/v1/accounts/{id}/contacts` - List/create/update contacts
- `/api/v1/accounts/{id}/conversations` - List/get/update conversations
- `/api/v1/accounts/{id}/conversations/{id}/messages` - Get/send messages
- `/api/v1/accounts/{id}/inboxes` - List inboxes
- `/api/v1/accounts/{id}/labels` - List labels
- `/api/v1/accounts/{id}/teams` - List teams

## Test Data

Initial test data loaded from `fixtures/` directory:
- `contacts.json` - Sample contacts
- `conversations.json` - Sample conversations
- `conversation_{id}_messages.json` - Messages for each conversation

## Error Simulation

Test error handling with:
- `/api/v1/accounts/{id}/test/401` - Unauthorized
- `/api/v1/accounts/{id}/test/429` - Rate limit
- `/api/v1/accounts/{id}/test/503` - Service unavailable

## Authentication

Mock server accepts any API token for testing. No real authentication required.

