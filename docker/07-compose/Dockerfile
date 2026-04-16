# Stage 1: Builder
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json .
COPY . .

# Stage 2: Runtime
FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/app.js .
COPY --from=builder /app/package.json .

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

CMD ["node", "app.js"]
