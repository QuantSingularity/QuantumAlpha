# Mobile Frontend Dockerfile for QuantumAlpha (fixed)
FROM node:18-alpine

# System deps (curl used by HEALTHCHECK)
RUN apk add --no-cache \
    bash \
    curl \
    git \
    python3 \
    make \
    g++

WORKDIR /app

# Copy package files for caching
COPY package*.json ./

# Deterministic install if lock exists, otherwise install
RUN if [ -f package-lock.json ]; then \
      npm ci --silent --no-audit --prefer-offline; \
    else \
      npm install --silent --no-audit --prefer-offline; \
    fi

# Ensure 'expo' CLI is available locally even if not declared in package.json
# This installs expo into node_modules without modifying package.json (no-save).
RUN if [ ! -d node_modules/expo ]; then \
      npm install --no-save expo@latest --silent --no-audit || true; \
    fi

# Copy source
COPY . .

# Fix permissions and switch to built-in node user
RUN chown -R node:node /app
USER node

# Metro / Expo ports
EXPOSE 8081 19000 19001 19002

# Health check hitting Metro's status endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/status || exit 1

# Start using local CLI via npx (recommended)
CMD ["npx", "expo", "start", "--tunnel", "--port", "8081"]