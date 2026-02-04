# AI Communications Hub - Complete Architecture

## Directory Structure

```
ai_comms_hub/
├── ai_comms_hub/                    # Main module
│   ├── __init__.py
│   ├── hooks.py                     # Frappe hooks
│   ├── modules.txt                  # Module list
│   │
│   ├── api/                         # Core API functionality
│   │   ├── __init__.py
│   │   ├── llm.py                  # ✅ LLM integration (naga.ac)
│   │   ├── functions.py            # ✅ Function calling handlers
│   │   ├── rag.py                  # ✅ RAG with Qdrant
│   │   ├── ai_engine.py            # ✅ AI response generation
│   │   └── message.py              # ✅ Message delivery across channels
│   │
│   ├── webhooks/                    # Webhook handlers
│   │   ├── __init__.py
│   │   ├── voice.py                # ✅ VAPI webhooks
│   │   ├── social.py               # ✅ Facebook, Instagram, Twitter
│   │   └── email_handler.py        # ✅ SendGrid inbound parse
│   │
│   ├── customer_support/            # Customer Support module
│   │   ├── __init__.py
│   │   └── doctype/
│   │       ├── communication_hub/   # ✅ Master conversation record
│   │       │   ├── communication_hub.json
│   │       │   ├── communication_hub.py
│   │       │   ├── communication_hub.js
│   │       │   └── __init__.py
│   │       │
│   │       ├── communication_message/ # ✅ Individual messages
│   │       │   ├── communication_message.json
│   │       │   ├── communication_message.py
│   │       │   ├── communication_message.js
│   │       │   └── __init__.py
│   │       │
│   │       └── ai_communications_hub_settings/ # ⏳ Settings DocType
│   │           ├── ai_communications_hub_settings.json
│   │           ├── ai_communications_hub_settings.py
│   │           ├── ai_communications_hub_settings.js
│   │           └── __init__.py
│   │
│   ├── utils/                       # ⏳ Utility functions
│   │   ├── __init__.py
│   │   ├── helpers.py              # Common helper functions
│   │   └── validators.py           # Data validation
│   │
│   ├── tasks/                       # ⏳ Scheduled tasks
│   │   ├── __init__.py
│   │   ├── hourly/
│   │   │   ├── __init__.py
│   │   │   └── sync_messages.py
│   │   ├── daily/
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py
│   │   │   └── cleanup.py
│   │   ├── weekly/
│   │   │   ├── __init__.py
│   │   │   └── reports.py
│   │   └── monthly/
│   │       ├── __init__.py
│   │       └── archive.py
│   │
│   ├── setup/                       # ⏳ Installation scripts
│   │   ├── __init__.py
│   │   ├── install.py              # Installation hooks
│   │   └── fixtures.py             # Default data
│   │
│   ├── scripts/                     # ⏳ Utility scripts
│   │   ├── setup_qdrant.py         # Qdrant collection setup
│   │   ├── migrate_data.py         # Data migration
│   │   └── test_integrations.py    # Integration tests
│   │
│   ├── config/                      # ⏳ Configuration
│   │   ├── __init__.py
│   │   └── n8n_workflows/          # n8n workflow templates
│   │       ├── voice_workflow.json
│   │       ├── facebook_workflow.json
│   │       ├── instagram_workflow.json
│   │       ├── twitter_workflow.json
│   │       ├── email_workflow.json
│   │       └── README.md
│   │
│   ├── public/                      # ⏳ Frontend assets
│   │   ├── css/
│   │   │   └── ai_comms_hub.css
│   │   └── js/
│   │       └── ai_comms_hub.js
│   │
│   ├── templates/                   # ⏳ Email/message templates
│   │   ├── email/
│   │   │   ├── welcome.html
│   │   │   └── notification.html
│   │   └── pages/
│   │
│   ├── tests/                       # ⏳ Test suite
│   │   ├── __init__.py
│   │   ├── unit/
│   │   │   ├── test_llm.py
│   │   │   ├── test_rag.py
│   │   │   └── test_functions.py
│   │   └── integration/
│   │       ├── test_voice_flow.py
│   │       ├── test_email_flow.py
│   │       └── test_social_flow.py
│   │
│   └── docs/                        # ⏳ Documentation
│       ├── installation.md
│       ├── configuration.md
│       ├── api_reference.md
│       └── troubleshooting.md
│
├── README.md                        # ✅ Project overview
├── pyproject.toml                   # ✅ Package configuration
├── LICENSE                          # ⏳ License file
└── ARCHITECTURE.md                  # ✅ This file
```

## Component Status

### ✅ Completed (35%)
- App structure (pyproject.toml, hooks.py, README.md)
- Communication Hub DocType (JSON, Python, JS)
- Communication Message DocType (JSON, Python, JS)
- Voice webhook handler (voice.py)
- Social media webhook handlers (social.py)
- Email webhook handler (email_handler.py)
- LLM integration (llm.py)
- Function calling (functions.py)
- RAG integration (rag.py)
- AI engine (ai_engine.py)
- Message delivery (message.py)

### ⏳ Pending (65%)
- Settings DocType
- Utility functions
- Scheduled tasks
- Installation scripts
- Qdrant setup scripts
- n8n workflow templates
- Database migration scripts
- Test suite
- Documentation
- Frontend assets

## Data Flow

### Inbound Message Flow
```
External Platform → Webhook → n8n → Frappe API → Communication Hub
                                                    ↓
                                            Communication Message
                                                    ↓
                                              AI Engine
                                                    ↓
                            RAG (Qdrant) ← LLM (naga.ac) → Function Calls
                                                    ↓
                                          AI Response Message
                                                    ↓
                                          Message Delivery
                                                    ↓
                                            External Platform
```

### AI Decision Tree
```
Message Received
    ↓
Autonomous Mode?
    ↓ Yes
RAG Search (if knowledge query)
    ↓
Generate LLM Response
    ↓
Function Call Needed?
    ↓ Yes → Execute Function → Return to LLM
    ↓ No
Confidence > 80%?
    ↓ Yes → Send Response
    ↓ No → Escalate to HITL
```

## Integration Points

### External Services
1. **naga.ac** - LLM and embeddings
2. **VAPI** - Voice AI
3. **Meta Graph API** - Facebook/Instagram
4. **Twitter API v2** - Twitter DMs
5. **SendGrid** - Email
6. **Chatwoot** - Live chat
7. **Twilio** - SMS/WhatsApp
8. **Qdrant** - Vector database

### Internal Systems
1. **ERPNext** - Customer, Sales Order, Quotation, Item
2. **n8n** - Workflow orchestration
3. **PostgreSQL** - Data storage
4. **Redis** - Caching/real-time

## Key Design Decisions

1. **Frappe as Brain** - Single source of truth, not just database
2. **n8n as Middleware** - Normalizes all platforms to unified format
3. **Qdrant for RAG** - Fast vector search for knowledge retrieval
4. **Platform-Specific Prompts** - AI adapts to channel constraints
5. **Three AI Modes**:
   - Autonomous: Full AI automation
   - HITL: AI asks human for guidance
   - Takeover: Human assumes control, AI assists

## Performance Targets

- Response time: < 3 seconds
- System uptime: > 99.5%
- AI resolution rate: > 80%
- RAG accuracy: > 85%
- Cost per conversation: < $0.50

## Security Considerations

1. **Webhook Verification** - Signature validation for all webhooks
2. **API Key Management** - Encrypted storage in Settings
3. **Rate Limiting** - Per-channel rate limits
4. **Data Encryption** - TLS for all API calls
5. **Access Control** - Role-based permissions

## Scaling Strategy

1. **Horizontal Scaling** - n8n workers can scale independently
2. **Queue Management** - Frappe background jobs for async processing
3. **Caching** - Redis for frequently accessed data
4. **Database Optimization** - Proper indexes on all query paths
5. **LLM Caching** - Cache common responses to reduce API costs

## Next Steps (Implementation Order)

1. ✅ Complete app structure
2. ✅ Create Communication Hub and Message DocTypes
3. ✅ Implement webhook handlers (voice, social, email)
4. ✅ Build API module (LLM, RAG, functions, ai_engine, message)
5. ⏳ Create Settings DocType
6. ⏳ Write installation scripts
7. ⏳ Set up Qdrant collections
8. ⏳ Create n8n workflow templates
9. ⏳ Add database indexes
10. ⏳ Write tests
11. ⏳ Complete documentation
12. ⏳ End-to-end testing

## File Completion Tracker

| Module | Files | Completed | Pending |
|--------|-------|-----------|---------|
| App Structure | 4 | 4 (100%) | 0 |
| DocTypes | 8 | 8 (100%) | 0 |
| Webhooks | 4 | 4 (100%) | 0 |
| API | 5 | 5 (100%) | 0 |
| Utils | 3 | 0 (0%) | 3 |
| Tasks | 7 | 0 (0%) | 7 |
| Setup | 3 | 0 (0%) | 3 |
| Scripts | 3 | 0 (0%) | 3 |
| Config | 7 | 0 (0%) | 7 |
| Templates | 4 | 0 (0%) | 4 |
| Tests | 7 | 0 (0%) | 7 |
| Docs | 4 | 0 (0%) | 4 |
| **Total** | **59** | **21 (36%)** | **38 (64%)** |

---

**Status**: Phase 0 Foundation - 36% Complete
**Next**: Settings DocType, Installation Scripts, n8n Templates
