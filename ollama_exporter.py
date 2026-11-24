import os
import time
import requests
from prometheus_client import start_http_server, Gauge

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
ollama_up = Gauge("ollama_up", "Whether the Ollama API is reachable")
ollama_models = Gauge("ollama_models", "Number of locally installed Ollama models")
ollama_running_models = Gauge("ollama_running_models", "Number of currently running Ollama models")


def collect():
    while True:
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            ollama_up.set(1)
            ollama_models.set(len(data.get("models", [])))
        except Exception:
            ollama_up.set(0)
            ollama_models.set(0)

        try:
            response = requests.get(f"{OLLAMA_URL}/api/ps", timeout=5)
            response.raise_for_status()
            ollama_running_models.set(len(response.json().get("models", [])))
        except Exception:
            ollama_running_models.set(0)

        time.sleep(15)


if __name__ == "__main__":
    import threading
    start_http_server(int(os.getenv("EXPORTER_PORT", "9108")))
    threading.Thread(target=collect, daemon=True).start()
    while True:
        time.sleep(3600)
