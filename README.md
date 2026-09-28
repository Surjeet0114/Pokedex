# Pokédex

A small full-stack Pokédex for searching Pokémon, comparing stats, and keeping account-based favorites and search history.

## Architecture

```text
Browser → Flask web app → Spring Boot API → PostgreSQL
                   └──→ PokéAPI
```

- **Flask** renders the pages, talks to PokéAPI, and forwards account data requests to Spring Boot.
- **Spring Boot** handles registration, login, JWT validation, user profile, favorites, and search history.
- **PostgreSQL** persists users, favorites, and search history. PokéAPI supplies Pokémon data.
- The browser talks only to Flask. Flask sends the JWT as a Bearer token when it calls protected Java endpoints.

## Features

- Search by Pokémon name or Pokédex number
- Pokémon artwork, types, base stats, abilities, moves, cries, and complete evolution branches
- Side-by-side Pokémon comparisons
- BCrypt password hashing and signed JWT authentication
- User profile, favorites, and the most recent 50 searches
- CSRF-protected Flask forms and secure session cookie defaults

## Project structure

```text
flask-app/
  app/                 Flask app factory, routes, and API clients
  static/              CSS and fallback artwork
  templates/           Jinja pages
  tests/               Flask route and form tests
  Dockerfile
java-backend/
  src/main/java/       Spring controllers, services, DTOs, security, entities
  src/main/resources/  PostgreSQL and application configuration
  src/test/java/       Spring API integration tests using H2
  Dockerfile
docker-compose.yml     PostgreSQL, Spring Boot, and Flask stack
Jenkinsfile            Test and image-build pipeline
```

## Prerequisites

For local development, install Python 3.11+, Java 21+, Maven 3.9+, and PostgreSQL 15+. Docker Compose is optional for local development and can run the full stack without a local PostgreSQL installation.

## Local setup

### PostgreSQL

Create a database and application user using `psql` or another PostgreSQL client:

```sql
CREATE USER pokedex WITH PASSWORD 'pokedex';
CREATE DATABASE pokedex OWNER pokedex;
```

The credentials above are for local development only. Configure `DB_URL`, `DB_USERNAME`, and `DB_PASSWORD` if your local database uses different values.

### Spring Boot API

In PowerShell, set a development JWT key for the current terminal and start the API:

```powershell
$env:JWT_SECRET = 'replace-this-with-a-random-secret-of-at-least-32-bytes'
cd java-backend
mvn spring-boot:run
```

The API runs on `http://localhost:8080`. JPA schema updates are enabled for development. Set `JPA_DDL_AUTO` to a managed migration strategy for production deployments.

### Flask web app

In another terminal:

```powershell
cd flask-app
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:FLASK_SECRET_KEY = 'replace-this-with-a-random-session-secret'
$env:JAVA_API_URL = 'http://localhost:8080'
py run.py
```

Open `http://localhost:5000`. `FLASK_SECRET_KEY` must stay stable between restarts if sessions should remain valid. For HTTPS, set `SESSION_COOKIE_SECURE=true`.

### Environment variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `DB_URL` | Java | PostgreSQL JDBC URL; defaults to `localhost:5432/pokedex` |
| `DB_USERNAME`, `DB_PASSWORD` | Java, Compose | Database credentials |
| `JWT_SECRET` | Java, Compose | HMAC signing key; provide a random value of at least 32 bytes |
| `JWT_EXPIRATION_MS` | Java | JWT lifetime; defaults to one day |
| `JPA_DDL_AUTO` | Java | Hibernate schema mode; defaults to `update` for development |
| `CORS_ORIGIN` | Java, Compose | Allowed browser origin for API calls |
| `FLASK_SECRET_KEY` | Flask, Compose | Signs Flask session cookies |
| `SESSION_COOKIE_SECURE` | Flask, Compose | Sends the session cookie only over HTTPS when `true` |
| `JAVA_API_URL` | Flask | Spring API base URL; defaults to `http://localhost:8080` |
| `WEB_PORT` | Compose | Host port for Flask; defaults to `5000` |

## Run the complete stack with Docker Compose

Docker is optional; this is a convenient alternative to installing PostgreSQL, Java, and Python locally.

1. Copy `.env.example` to `.env` and replace the sample database password, JWT key, and Flask key with unique values.
2. Run `docker compose up --build` from the repository root.
3. Open `http://localhost:5000`.

Compose waits for PostgreSQL to become healthy before starting Spring Boot, then waits for the API health endpoint before starting Flask. The `postgres_data` volume persists database data. `docker compose down` keeps it; `docker compose down -v` deletes it.

The database and API ports are not published to the host. For a public deployment, place Flask behind a TLS reverse proxy, set `SESSION_COOKIE_SECURE=true`, use strong secrets, and use managed database migrations instead of automatic schema updates.

## API overview

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Public | Backend health |
| `POST` | `/api/auth/register` | Public | Create account and return JWT |
| `POST` | `/api/auth/login` | Public | Authenticate and return JWT |
| `GET` | `/api/users/me` | JWT | Current user profile |
| `GET`, `POST` | `/api/users/history` | JWT | List or record search history |
| `GET`, `POST` | `/api/users/favorites` | JWT | List or save favorites |
| `DELETE` | `/api/users/favorites/{pokemonId}` | JWT | Remove a favorite |

Registration validates username, email, and password, checks for duplicate accounts, stores normalized email, and hashes the password with BCrypt. Protected routes require `Authorization: Bearer <token>`. User, favorite, and history responses use DTOs and never include the password hash.

## Tests and CI

Run the Flask suite:

```powershell
cd flask-app
py -m pytest -q
```

Run the Java compile and integration suite:

```powershell
cd java-backend
mvn clean test
```

The Java integration tests use an in-memory H2 database; the running application uses PostgreSQL. The root `Jenkinsfile` runs both suites and builds the two Docker images. Jenkins needs a Linux agent with Python 3, Java 21, Maven 3.9+, Docker CLI, and a Docker daemon.
