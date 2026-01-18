import json
import os

CONFIG_FILE = "config.json"

# Default settings if file doesn't exist
DEFAULT_CONFIG = {
    "appearance_mode": "System",  # System, Dark, Light
    "color_theme": "blue",        # blue, green, dark-blue
    "notifications_enabled": True
}

class ConfigManager:
    _instance = None

    def __new__(cls):
        # Singleton pattern to ensure only one config instance exists
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        """Loads config from JSON file or creates default"""
        if not os.path.exists(CONFIG_FILE):
            self.config = DEFAULT_CONFIG.copy()
            self.save_config()
        else:
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
                    # Merge with default to ensure all keys exist (for updates)
                    for key, val in DEFAULT_CONFIG.items():
                        if key not in self.config:
                            self.config[key] = val
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = DEFAULT_CONFIG.copy()

    def save_config(self):
        """Saves current config to JSON file"""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save_config()