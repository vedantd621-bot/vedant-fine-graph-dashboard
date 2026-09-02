# Multi-stage build for React Dashboard
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# Production Nginx server
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
