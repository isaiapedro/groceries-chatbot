# PIOS Grocery Manager

Grocery Manager accepts WhatsApp Cloud API text messages, categorizes grocery
items, and persists them in PostgreSQL. It can also issue a short-lived
shopping checklist link from a WhatsApp conversation.

## Components

- `src/lambda_function.py`: API Gateway/Lambda handler and Meta integration.
- `src/parser.py` and `src/categories.py`: command parsing and classification.
- `src/db.py`, `src/models.py`, and `src/crud.py`: PostgreSQL persistence.
- `config/migration.sql`: clean database schema migration.
- `config/deploy.sh`: AWS packaging and deployment script.

## Deployment prerequisites

Apply `config/migration.sql` with the database's administrative migration
workflow. Before running `config/deploy.sh` from `config/`, export all required
environment variables listed in [API.md](API.md). Secrets are not read from
files or written by the deployment script.

The webhook endpoint is public solely so Meta can invoke it. `POST /webhook`
accepts only requests carrying a valid `X-Hub-Signature-256` calculated with
`META_APP_SECRET`. Configure the deployment URL in the Meta WhatsApp Cloud API
webhook settings and use the same `VERIFY_TOKEN` for subscription verification.

## Local development

Install the pinned dependencies from `config/requirements.txt`, configure the
required environment variables, and run the desired module from `src/`. Do not
place credentials in the repository or commit local configuration files.

See [API.md](API.md), [ARCHITECTURE.md](ARCHITECTURE.md), and
[DECISIONS.md](DECISIONS.md) for the current operational contract.
