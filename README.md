# HubSpot CRM Service

**Table of Contents:**
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation & Setup Instructions](#installation--setup-instructions)
5. [Environment Variables](#environment-variables)
6. [Docker Deployment](#docker-deployment)
7. [Running the App (Non-Docker)](#running-the-app-non-docker)
8. [Swagger Documentation](#swagger-documentation)
9. [API Endpoints & Usage](#api-endpoints--usage)
   - [Contact Endpoints](#contact-endpoints)
   - [Deal Endpoints](#deal-endpoints)
   - [Ticket Endpoints](#ticket-endpoints)
   - [Retrieve Newly Created Objects](#retrieve-newly-created-objects)
10. [Authentication Details (HubSpot OAuth)](#authentication-details-hubspot-oauth)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)
13. [License](#license)

---

## Project Overview

This **HubSpot CRM Service** provides a **Flask**-based integration with HubSpot’s CRM, focusing on:
- **Contact Management**: Create or update contacts in HubSpot.
- **Deal Management**: Create or update deals, associated with contacts.
- **Ticket Management**: Create new support tickets and associate them with contacts and deals.
- **Data Retrieval**: Fetch newly created CRM objects (contacts, deals, tickets) with pagination.

### Why This Project?

- **Automates** the creation and linkage of core HubSpot CRM objects.
- **Centralizes** HubSpot OAuth token management and refresh logic.
- **Enables** seamless Docker-based deployment for consistent environments.

---

## Features

1. **HubSpot OAuth** with automatic **token refresh**.
2. **Create or update** HubSpot **contacts** and **deals** based on mandatory fields.
3. **Create** new **tickets** (never update) linked to a contact & deal(s).
4. **Retrieve** newly created contacts, deals, and tickets with pagination.
5. **Customizable** environment variables (`.env`) for storing OAuth credentials and other config.

---

## Prerequisites

- **Python 3.9+** (if running locally without Docker)
- **Docker** & **Docker Compose** (if running in containers)
- A **HubSpot Developer Account** or valid HubSpot credentials (Client ID, Client Secret, Refresh Token)

---

## Installation & Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Osaroigb/hubspot-crm-service.git
   cd hubspot-crm-service
   ```

2. **Copy `.env.example` to `.env`**:
   ```bash
   cp .env.example .env
   ```
   Then **edit** `.env` to add your real **HubSpot** Client ID, Client Secret, and Refresh Token:
   ```bash
   HUBSPOT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   HUBSPOT_CLIENT_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   HUBSPOT_REFRESH_TOKEN=na1-...
   ```

3. **(Optional) Customize Ports**  
   By default, the Flask app runs on port **8080**. If you need to change it, edit `APP_PORT` in your `.env` file and also update the **docker-compose.yml** if necessary.

4. **Install Dependencies** (only if running outside Docker):
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## Environment Variables

All environment variables are defined in **`.env.example`**. Copy them into **`.env`** and fill in appropriate values. Key variables:

- **`APP_HOST`**: The host (e.g. `0.0.0.0`)  
- **`APP_PORT`**: The Flask port (e.g. `8080`)  
- **`APP_NAME`**: A name for the application (e.g. `HubSpot CRM Service`)
- **`APP_ENV`**: The environment (e.g. `development`, `production`)  
- **`HUBSPOT_CLIENT_ID`**: Your HubSpot OAuth client ID  
- **`HUBSPOT_CLIENT_SECRET`**: Your HubSpot OAuth client secret  
- **`HUBSPOT_REFRESH_TOKEN`**: Your HubSpot OAuth refresh token  

Ensure these are **not** committed to version control by checking your **`.gitignore`**.

---

## Docker Deployment

### 1. Build & Run via Docker Compose

Make sure you have Docker & Docker Compose installed. Then simply run:
```bash
docker-compose up --build
```

This will:
1. Build the **Flask** image from the **`Dockerfile`**.
2. Start a container named **`hubspot_crm_api`** (or whichever name you specified in `docker-compose.yml`).
3. Expose port **8080** (by default), so the API is accessible at `http://localhost:8080/api/v1`.

### 2. Verify

Once the container logs show “Running on 0.0.0.0:8080”, open another terminal or Postman to **test**:

```bash
curl http://localhost:8080/api/v1
```
(Or your other endpoints below.)

### 3. Stop the Container

Use `CTRL+C` in the same terminal or:
```bash
docker-compose down
```

---

## Running the App (Non-Docker)

If you prefer **not** to use Docker:

1. **Create and activate** a Python virtual environment.
2. **Install** dependencies from `requirements.txt`.
3. **Run** the app:
   ```bash
   python run.py
   ```
4. The API will be available at:
   ```
   http://127.0.0.1:8080/api/v1
   ```

---

## Swagger Documentation

The API comes with built-in **Swagger UI** documentation via **Flasgger**.

- **Interactive UI**: [http://127.0.0.1:8080/api-docs/](http://127.0.0.1:8080/api-docs/)
- **Raw JSON Spec**: [http://127.0.0.1:8080/api-docs/apispec.json](http://127.0.0.1:8080/api-docs/apispec.json)

This UI allows you to explore, test, and view schema definitions for all available routes.

---

## API Endpoints & Usage
📌 [Postman API Docs](https://documenter.getpostman.com/view/14515325/2sAYkGMKoE) for a more detailed API documentatoin of all the endpoints including request and responses.

Below is a **high-level** overview of the main endpoints. Full reference is in the code or docstrings.

### Contact Endpoints

- **`POST /api/v1/hubspot/contact`**

  **Purpose**: Create or update a HubSpot contact.  
  **Body** (JSON):
  ```json
  {
    "email": "johndoe@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "phone": "+1234567890",
    "extra_field": "any extra data"
  }
  ```
  **Responses**:
  - `200 OK`: Contact created or updated successfully.
  - `422 Unprocessable Entity`: Invalid input data.
  - `400 / 401 / ...`: HubSpot error.

### Deal Endpoints

- **`POST /api/v1/hubspot/deals`**

  **Purpose**: Create or update one or more deals, associating them with a **contact**.  
  **Body** (JSON):
  ```json
  {
    "contactId": "CONTACT_ID",
    "deals": [
      {
        "dealname": "My Awesome Deal",
        "amount": 999.99,
        "dealstage": "appointmentscheduled"
      },
      {
        "dealname": "Another Big Deal",
        "amount": 1200,
        "dealstage": "qualifiedtobuy",
        "extra_field": "custom value"
      }
    ]
  }
  ```
  **Response**: An array of created/updated deals.

### Ticket Endpoints

- **`POST /api/v1/hubspot/tickets`**

  **Purpose**: Create one or more new support tickets, always new (never update).  
  **Body** (JSON):
  ```json
  {
    "contactId": "107732990328",
    "dealIds": ["34904505483"],
    "tickets": [
      {
        "subject": "Issue with subscription",
        "description": "Payment processed but no access",
        "category": "billing",
        "pipeline": "tickets-pipeline",
        "hs_ticket_priority": "HIGH",
        "hs_pipeline_stage": "1"
      }
    ]
  }
  ```
  **Response**: An array of the newly created ticket objects.

### Retrieve Newly Created Objects

- **`GET /api/v1/hubspot/new-objects?since=2025-03-20T00:00:00Z&limit=5&after=NTk`**

  **Purpose**: Retrieve newly created contacts (with associated deals), deals, and tickets since a given timestamp.  
  **Query Params**:
  - `since` (required): e.g. `2025-03-20T00:00:00Z`
  - `limit` (optional): default 10
  - `after` (optional): paging cursor from previous response.  

  
  **Response**:
  ```json
  {
    "success": true,
    "message": "Retrieved newly created CRM objects.",
    "data": {
      "contacts": [...],
      "deals": [...],
      "tickets": [...],
      "contacts_paging": {...},
      "deals_paging": {...},
      "tickets_paging": {...}
    }
  }
  ```

---

## Authentication Details (HubSpot OAuth)

This application uses **OAuth** credentials to access HubSpot. In `.env`, you must provide:
- **HUBSPOT_CLIENT_ID**
- **HUBSPOT_CLIENT_SECRET**
- **HUBSPOT_REFRESH_TOKEN**

The app automatically **refreshes** the access token when expired. For details:
1. On startup or first request, the service exchanges **refresh_token** for an **access_token**.
2. All subsequent HubSpot API calls include **Bearer** tokens in the `Authorization` header.
3. If HubSpot returns **401**, the token is refreshed again.

If these environment variables are missing or invalid, you’ll see errors like **`Invalid or expired HubSpot refresh token`** in logs or a 401.

---

## Testing

### ✅ Unit & Integration Tests

This project uses **pytest** to run both **unit tests** and **integration tests**.

To run all tests:
```bash
pytest
```

Tests are located in the `tests/` directory:
- `tests/unit/`: Unit tests for services and utilities
- `tests/integration/`: Integration tests for endpoint logic

These test cases include edge conditions, mocking of external APIs, and service interactions.

---

## Troubleshooting

1. **Missing Environment Variables**  
   - If the service fails to start, ensure `.env` has all **required** fields (`HUBSPOT_CLIENT_ID`, etc.).  
   - Double-check you didn’t commit the `.env` file to source control accidentally.

2. **HubSpot 400 or 404 Errors**  
   - The logs typically show a JSON response from HubSpot. For example, `"Property \"extra_field\" does not exist"` indicates you’re passing a field that doesn’t exist in your HubSpot schema.  
   - A 404 for deals or contacts might mean an invalid ID.

3. **Docker** Fails to Build  
   - Check Docker logs. Ensure `requirements.txt` references valid packages.  
   - Confirm you have an updated Docker version.

4. **Rate Limit (429)**  
   - If you’re making too many calls quickly, you may see `429` from HubSpot. The code attempts exponential backoff. If that fails, you may have to reduce call volume or request higher limits from HubSpot.

5. **Time Zone or Date Format**  
   - The `since` parameter must be in a valid **ISO 8601** date-time string with `Z` for UTC. Example: `"2025-03-20T00:00:00Z"`.

6. **Local Dev vs Production**  
   - For local dev, you can mount volumes if you want hot-reloading. For production, consider using a more robust WSGI server like Gunicorn or hosting behind a reverse proxy (Nginx or Traefik).

---

## License

This project is licensed under the [MIT License](LICENSE). Feel free to modify and distribute as you see fit.

---

**Enjoy your fully Dockerized HubSpot CRM Service!** If you have any questions or issues, open a GitHub issue or refer to the [HubSpot developer docs](https://developers.hubspot.com/docs).
