# Project plan

This project intentionally starts as a small full-stack application rather than a microservice platform.

## Current

- Flask UI
- Python PokeAPI integration
- Spring Boot user/API backend
- PostgreSQL
- JWT authentication
- Favorites
- User-specific history
- HTML/CSS/Bootstrap UI

## In place

- Docker Compose development stack with persistent PostgreSQL storage
- Jenkins checks for Flask and Spring Boot, plus container image builds

## Later

Only add infrastructure when it solves a real problem:

1. Flyway migrations
2. Broader automated test coverage
3. Container registry publishing and deployment
4. Kubernetes only as an optional learning/deployment exercise
5. Resilience patterns around external services when needed
