# Docker Essential Training — Engine v29

8 hands-on exercises covering the full Docker workflow.

## Exercises

| # | Topic | Files |
|---|-------|-------|
| 01 | Installation & Setup | commands only |
| 02 | [Images — Build & Manage](./02-images/) | `app.js`, `Dockerfile` |
| 03 | Containers — Run & Inspect | commands only |
| 04 | Networking | commands only |
| 05 | [Volumes & Persistent Storage](./05-volumes/) | `app.js` |
| 06 | [Dockerfile Best Practices](./06-best-practices/) | multi-stage `Dockerfile` |
| 07 | [Docker Compose](./07-compose/) | full-stack `compose.yaml` |
| 08 | Production & Security | commands only |

## Quick start — Exercise 7 (Compose)

```bash
cd 07-compose
docker compose up -d --build
curl http://localhost:3000
docker compose down -v
```
