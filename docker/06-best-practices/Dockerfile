# Stage 1: Builder — prepares files, thrown away after
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json .
COPY . .

# Stage 2: Runtime — only what we actually need
FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/app.js .
COPY --from=builder /app/package.json .

# Security: never run as root in production
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

CMD ["node", "app.js"]
