# Inventory Sync Engine

Real-time inventory management system preventing overselling via SQL-level optimistic locking and idempotent webhook processing.

Built with Python, FastAPI, PostgreSQL, and Docker.

## Features

- Race condition prevention (handles concurrent requests safely)
- Idempotent webhook processing (safe duplicate request handling)
- Two-stage stock reservation system (prevents cart abandonment issues)
- Docker deployment
- Async PostgreSQL

## Architecture


## Tech Stack
Framework: Python 3.11, FastAPI, uvicorn
ORM: SQLAlchemy 2.0, asyncpg
Database: PostgreSQL 15
Deployment: Docker, Docker Compose
API Documentation: Swagger/OpenAPI UI

##Quick Start
#Prerequisites
Docker Desktop installed
git clone'd this repository
Installation

# Clone and navigate to project directory
git clone https://github.com/vondevnz/inventory-sync-engine.git
cd inventory-sync-engine

# Build and start containers
docker-compose up --build -d

# Wait ~30 seconds for database to initialize

# Verify app is running
curl http://localhost:8000/

##Access API Documentation

Open in browser:
http://localhost:8000/docs