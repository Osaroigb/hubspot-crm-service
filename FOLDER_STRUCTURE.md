hubspot-crm-service/
│
├── app/
│   │
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   │
│   ├── controllers/
│   │   └── hubspot_controller.py
│   │
│   ├── integrations/
│   │   └── hubspot_api.py
│   │
│   ├── schemas/
│   │   └── hubspot_schema.py
│   │
│   ├── services/
│   │   ├── hubspot_service.py
│   │   └── oauth_manager.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── api_responses.py
│       ├── constants.py
│       ├── errors.py
│       └── rate_limiting.py
│
├── tests/
│   ├── conftest.py
│   ├── integration/
│   │   ├── test_contact_endpoint.py
│   │   ├── test_deals_endpoint.py
│   │   ├── test_new_crm_endpoint.py
│   │   └── test_tickets_endpoint.py
│   │
│   └── unit/
│       ├── test_hubspot_service.py
│       ├── test_oauth_manager.py
│       └── test_rate_limiter.py
│
├── venv/
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── FOLDER_STRUCTURE.md
├── LICENSE
├── pytest.ini
├── README.md
├── requirements.txt
└── run.py
