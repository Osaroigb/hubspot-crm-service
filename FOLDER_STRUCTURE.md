hubspot-crm-service/
│
├── app/
│   │
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   │
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── hubspot_controller.py
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── hubspot_api.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── hubspot_schema.py
│   │
│   ├── services/
│   │   ├── __init__.py
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
│   ├── __init__.py
│   └── test_hubspot.py
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
├── README.md
├── requirements.txt
└── run.py
