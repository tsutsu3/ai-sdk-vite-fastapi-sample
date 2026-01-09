# 1. Frontend build stage
FROM node:22 AS frontend-build

WORKDIR /frontend

RUN corepack enable && corepack prepare pnpm@10.22.0 --activate

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend .

# RUN pnpm build
RUN pnpm build:nocheck

# 2. Backend build stage
FROM python:3.13-slim AS backend-build

WORKDIR /backend

COPY backend/pyproject.toml backend/requirements.lock ./
COPY backend .
# RUN pip install --no-cache-dir -r requirements.lock
RUN pip install --no-cache-dir .[duck,azure]

COPY --from=frontend-build /frontend/dist /backend/frontend/dist

# 3. Final image
FROM python:3.13-slim

WORKDIR /app

COPY --from=backend-build /backend /app
COPY --from=backend-build /usr/local /usr/local

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]