FROM python:3.12-alpine
WORKDIR /app
COPY . .
EXPOSE 2575
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "2575", "--log", "/app/logs/bridge.log"]

