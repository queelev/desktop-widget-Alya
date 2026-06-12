"""
Модуль управления настройками приложения
"""

import json
import os

class SettingsManager:
    DEFAULT_SETTINGS = {
        "notes_height": 140,
        "auto_start": False,
        "theme": "light"
    }
    
    def __init__(self, settings_file="data/settings.json"):
        self.settings_file = settings_file
        self.settings = self.load_settings()
    
    def load_settings(self):
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    merged = self.DEFAULT_SETTINGS.copy()
                    merged.update(loaded)
                    return merged
            except:
                pass
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def get_setting(self, key, default=None):
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()