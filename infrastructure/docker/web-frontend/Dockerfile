# ---- Build stage ----
FROM node:20-alpine AS builder

WORKDIR /build

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# ---- Runtime stage ----
FROM nginx:1.25-alpine AS runtime

RUN addgroup -g 101 -S nginx 2>/dev/null || true \
    && adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx 2>/dev/null || true \
    && rm -f /etc/nginx/conf.d/default.conf

COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

RUN chown -R nginx:nginx /usr/share/nginx/html \
    && chmod -R 755 /usr/share/nginx/html \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

USER 101:101

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
