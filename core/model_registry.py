import json
from pathlib import Path
from google import genai
import random

class ModelRegistry:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.keys = []
        self.load_keys()
        
        # Model Definitions
        self.models = {
            "CEO": "models/gemini-2.5-flash-native-audio-preview-12-2025",
            "CTO": "models/gemma-4-31b-preview",
            "RESEARCHER": "models/gemini-2.5-pro",
            "ANALYST": "models/gemini-3.1-flash-lite",
            "CREATIVE": "models/imagen-4",
            "COMPUTER_USE": "models/computer-use-preview"
        }
        
        self._clients = {}

    def load_keys(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.keys = config.get("gemini_api_keys", [])
                if not self.keys and "gemini_api_key" in config:
                    self.keys = [config["gemini_api_key"]]
        except Exception as e:
            print(f"[ModelRegistry] Error loading keys: {e}")
            self.keys = []

    def get_client(self, model_key="CEO"):
        if not self.keys:
            return None
            
        # Use a random key to distribute load (simple load balancing)
        api_key = random.choice(self.keys)
        
        # In a real scenario, we might want to cache clients per key or model
        # For now, we'll return a fresh client with a chosen key
        return genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

    def get_model_name(self, role):
        return self.models.get(role.upper(), self.models["CEO"])

registry = None

def init_registry(config_path: Path):
    global registry
    registry = ModelRegistry(config_path)
    return registry

def get_registry():
    return registry
