import os
import json

class OllamaClient:
    def __init__(self, host=None):
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def _post(self, endpoint, payload):
        import requests # Import requests inside the method
        url = f"{self.host}{endpoint}"
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint):
        import requests # Import requests inside the method
        url = f"{self.host}{endpoint}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def generate(self, model, prompt, stream=False, **kwargs):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs
        }
        return self._post("/api/generate", payload)

    def chat(self, model, messages, stream=False, **kwargs):
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        return self._post("/api/chat", payload)

    def embeddings(self, model, prompt):
        payload = {
            "model": model,
            "prompt": prompt
        }
        return self._post("/api/embeddings", payload)

    def pull_model(self, model):
        import requests # Import requests inside the method
        url = f"{self.host}/api/pull"
        payload = {
            "name": model,
            "stream": True
        }
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    try:
                        yield json.loads(chunk.decode('utf-8'))
                    except json.JSONDecodeError:
                        pass

    def list_models(self):
        return self._get("/api/tags")
