import json
import requests
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with a local Ollama instance."""
    
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def list_models(self):
        """Get list of available models from Ollama."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    def generate(self, model, prompt, system_prompt=None, history=None, temperature=0.7, max_tokens=500):
        """Generate a response from Ollama."""
        # Prepare messages
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        if history:
            for msg in history:
                messages.append(msg)
        
        # Add the current user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                data=json.dumps(payload)
            )
            response.raise_for_status()
            result = response.json()
            return result.get('message', {}).get('content', "No response from model.")
        except requests.exceptions.ConnectionError:
            return "❌ Error: Cannot connect to Ollama server. Please ensure it's running."
        except requests.exceptions.Timeout:
            return "❌ Error: Ollama server timed out. The model might be loading."
        except Exception as e:
            logger.error(f"Ollama generation error: {str(e)}")
            return f"❌ Error generating response: {str(e)}"
