# Essential Training Series

Hands-on lab guides for modern DevOps tooling — one command at a time.

> Follow along on [LinkedIn](https://www.linkedin.com/in/mohtadinasri/) | GitHub: [@MohtadiNasri](https://github.com/MohtadiNasri)

---

## Courses

| # | Course | Engine | Exercises | Duration | Level |
|---|--------|--------|-----------|----------|-------|
| 01 | [Docker](./docker/) | v29 | 8 | 4h | Beginner+ |
| 02 | [Docker Compose](./docker-compose/) | v2 | 8 | 4h | Intermediate |
| 03 | [k3s](./k3s/) | v1.x | — | — | Coming soon |
| 04 | [Helm](./helm/) | v3 | — | — | Coming soon |

---

## How to use

Each course folder contains one sub-folder per exercise with all the files you need.  
No copy-pasting from PDFs — every file is ready to use.

```bash
git clone https://github.com/MohtadiNasri/essential-training-series.git
cd essential-training-series/docker/07-compose
docker compose up -d
```

---

## Series structure

```
essential-training-series/
├── docker/
│   ├── 02-images/
│   ├── 05-volumes/
│   ├── 06-best-practices/
│   └── 07-compose/
├── docker-compose/
│   ├── 01-first-stack/
│   ├── 02-build-dev/
│   ├── 03-networks/
│   ├── 04-volumes/
│   ├── 05-healthchecks/
│   ├── 06-profiles/
│   ├── 07-scaling/
│   └── 08-debugging/
├── Docs Essential Training/
│   ├── Docker_Essential_Training.pdf
│   └── DockerCompose_Essential_Training.pdf
├── helm/
└── k3s/
```

---

*"Learn by doing. One command at a time."*
