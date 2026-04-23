# K3s Essential Training — Lightweight Kubernetes in Production

8 hands-on exercises covering the full K3s workflow.

> Follow along on [LinkedIn](https://www.linkedin.com/in/mohtadinasri/) | GitHub: [@MohtadiNasri](https://github.com/MohtadiNasri)

## Exercises

| # | Topic | Files |
|---|-------|-------|
| 01 | Installation & Configuration | commands only |
| 02 | Multi-Node Cluster | commands only |
| 03 | [Kubernetes Deployments](./03-deployments/) | `nginx-deploy.yaml` |
| 04 | [Ingress & Traefik](./04-ingress/) | `nginx-ingress.yaml` |
| 05 | [Persistent Storage](./05-storage/) | `postgres-pvc.yaml`, `postgres-deploy.yaml` |
| 06 | Secrets & ConfigMaps | commands only |
| 07 | Monitoring & Debugging | commands only |
| 08 | [High Availability](./08-ha/) | `resource-quota.yaml` |

## Quick start

```bash
# Exercise 3 — Deploy NGINX
cd 03-deployments
kubectl apply -f nginx-deploy.yaml
kubectl get pods -l app=nginx-demo -o wide

# Exercise 4 — Ingress
cd 04-ingress
kubectl apply -f nginx-ingress.yaml
kubectl get ingress

# Exercise 5 — Storage
cd 05-storage
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-deploy.yaml
kubectl get pvc

# Exercise 8 — HA quota
cd 08-ha
kubectl apply -f resource-quota.yaml
```

