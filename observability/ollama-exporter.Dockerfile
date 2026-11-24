FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir requests prometheus-client
COPY ollama_exporter.py /app/ollama_exporter.py
EXPOSE 9108
CMD ["python", "-u", "ollama_exporter.py"]
