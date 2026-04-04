FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY awscope/ ./awscope/
EXPOSE 8080
# Cache file must be mounted at /app/cache.json at runtime
ENV AWSCOPE_CACHE_PATH=/app/cache.json
CMD ["uvicorn", "awscope.web:app", "--host", "0.0.0.0", "--port", "8080"]
