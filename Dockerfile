FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV STATIC_EXPORT=1
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.lock.txt /app/backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt
COPY backend /app/backend
COPY scripts /app/scripts
COPY sql /app/sql
COPY --from=frontend-build /frontend/out /app/frontend/out
RUN useradd --create-home app && mkdir -p /app/data/raw /app/data/clean && chown -R app:app /app
USER app
ENV STATIC_DIR=/app/frontend/out
EXPOSE 10000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
