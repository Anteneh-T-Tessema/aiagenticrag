# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend & Final Image
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY agents/ ./agents/
COPY api/ ./api/
COPY core/ ./core/
COPY data/ ./data/
COPY mcp_servers/ ./mcp_servers/
COPY main.py .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# HF Spaces runs as a non-root user
RUN useradd -m -u 1000 user
USER user

ENV PYTHONUNBUFFERED=1
ENV PORT=7860

EXPOSE 7860

CMD ["uvicorn", "api.server:server", "--host", "0.0.0.0", "--port", "7860"]
