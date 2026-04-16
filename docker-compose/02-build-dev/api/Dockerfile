FROM node:22-alpine
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
CMD ["node", "app.js"]
