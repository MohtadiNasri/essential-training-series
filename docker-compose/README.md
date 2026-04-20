# Docker Compose Essential Training — Multi-Container Applications

8 hands-on exercises covering the full Compose workflow.

> Follow along on [LinkedIn](https://www.linkedin.com/in/mohtadinasri/) | GitHub: [@MohtadiNasri](https://github.com/MohtadiNasri)

## Exercises

| # | Topic | Files |
|---|-------|-------|
| 01 | [Your First Stack](./01-first-stack/) | `compose.yaml` |
| 02 | [Build & Dev Workflow](./02-build-dev/) | `compose.yaml`, `compose.override.yaml`, `compose.prod.yaml`, `api/` |
| 03 | [Networks & Service Discovery](./03-networks/) | `compose.yaml` |
| 04 | [Volumes & Data Management](./04-volumes/) | `compose.yaml` |
| 05 | [Health Checks & Dependencies](./05-healthchecks/) | `compose.yaml` |
| 06 | [Profiles & Environment Mgmt](./06-profiles/) | `compose.yaml`, `.env`, `.env.example` |
| 07 | [Scaling & Production](./07-scaling/) | `compose.yaml` |
| 08 | [Monitoring & Debugging](./08-debugging/) | `compose.yaml` |

## Quick start

```bash
# Run any exercise
cd 01-first-stack
docker compose up -d
docker compose ps
docker compose down

# Exercise 2 (dev with live reload)
cd 02-build-dev
cp .env.example .env     # only for ex06
docker compose up --build
```
