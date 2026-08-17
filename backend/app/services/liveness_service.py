# app/services/liveness_service.py
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import hashlib
from app.core.config import settings

logger = logging.getLogger(__name__)

class LivenessConfigService:
    """Liveness configuration management service"""
    
    def __init__(self, config_file: str = "liveness_config.json"):
        # Save in project root
        self.config_file = Path(__file__).parent.parent.parent / config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
        
        # Default values
        return {
            "enabled": False,
            "threshold": 0.5,
            "admin_password_hash": None,  # SHA256 hash storage
            "toggle_history": []
        }
    
    def _save_config(self):
        """Save config file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def set_admin_password(self, password: str):
        """Set admin password (for initial setup)"""
        self.config["admin_password_hash"] = self._hash_password(password)
        self._save_config()
        logger.info("Admin password has been set.")
    
    def verify_admin_password(self, password: str) -> bool:
        """Verify admin password"""
        if not self.config.get("admin_password_hash"):
            # If password not set, use password from .env
            if settings.LIVENESS_ADMIN_PASSWORD:
                # Use password from .env for initial setup
                expected_password = settings.LIVENESS_ADMIN_PASSWORD
                if password == expected_password:
                    self.set_admin_password(password)
                    logger.info("Admin password loaded from environment variable and set.")
                    return True
                else:
                    logger.warning("Password does not match LIVENESS_ADMIN_PASSWORD in .env.")
                    return False
            else:
                # If not in .env either, use first input as password
                self.set_admin_password(password)
                logger.info("First password input set as initial admin password.")
                return True
        
        password_hash = self._hash_password(password)
        return password_hash == self.config.get("admin_password_hash")
    
    def toggle_liveness(self, admin_password: str, enabled: bool) -> bool:
        """
        Toggle liveness mode
        
        Returns:
            True: Success, False: Password mismatch
        """
        if not self.verify_admin_password(admin_password):
            logger.warning("Liveness toggle failed: Admin password mismatch")
            return False
        
        old_enabled = self.config.get("enabled", False)
        self.config["enabled"] = enabled
        
        # Record history
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "enabled": enabled,
            "changed_from": old_enabled
        }
        self.config.setdefault("toggle_history", []).append(history_entry)
        
        # Keep only last 100 entries
        if len(self.config["toggle_history"]) > 100:
            self.config["toggle_history"] = self.config["toggle_history"][-100:]
        
        self._save_config()
        logger.info(f"Liveness mode changed: {old_enabled} -> {enabled}")
        return True
    
    def is_enabled(self) -> bool:
        """Check if liveness mode is enabled"""
        return self.config.get("enabled", False)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "enabled": self.config.get("enabled", False),
            "threshold": self.config.get("threshold", 0.5),
            "last_toggle": self.config.get("toggle_history", [])[-1] if self.config.get("toggle_history") else None
        }
    
    def get_toggle_history(self, limit: int = 20) -> list:
        """Get toggle history"""
        history = self.config.get("toggle_history", [])
        return history[-limit:] if limit > 0 else history


# Singleton instance
liveness_config_service = LivenessConfigService()
