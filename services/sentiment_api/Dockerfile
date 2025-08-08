FROM python:3.11-slim
WORKDIR /app
COPY ../../requirements-llm.txt /app/requirements-llm.txt
RUN pip install --no-cache-dir -r /app/requirements-llm.txt fastapi uvicorn
COPY . /app
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8082"]
