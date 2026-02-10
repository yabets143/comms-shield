import json
from pathlib import Path
from typing import Dict, Any

class Config:
    def __init__(self, config_path: Path = Path("config.json")):
        self.config_path = config_path
        self.default_config = {
            "watch_folders": [],
            "auto_start_watcher": False,
            "log_retention_days": 30,
            "backup_original_files": True,
            "supported_formats": [".jpg", ".jpeg", ".png", ".pdf", ".docx", ".xlsx"],
            "ui_theme": "dark"
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return {**self.default_config, **json.load(f)}
            except Exception:
                return self.default_config.copy()
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file"""
        if config:
            self.config = config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
    
    def add_watch_folder(self, folder_path: Path):
        """Add a folder to watch list"""
        watch_folders = self.get("watch_folders", [])
        if str(folder_path) not in watch_folders:
            watch_folders.append(str(folder_path))
            self.set("watch_folders", watch_folders)