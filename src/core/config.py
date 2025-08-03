import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration management for the Financial Analysis System."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._resolve_environment_variables()
        self._setup_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _resolve_environment_variables(self):
        """Resolve environment variables in configuration."""
        def resolve_value(value):
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                return os.environ.get(env_var, value)
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(v) for v in value]
            return value
        
        self._config = resolve_value(self._config)
    
    def _setup_directories(self):
        """Create necessary directories if they don't exist."""
        base_dir = self.config_path.parent.parent
        
        dirs_to_create = [
            self.get('paths.output_dir'),
            self.get('paths.raw_reports_dir'),
            self.get('paths.processed_data_dir'),
            self.get('paths.logs_dir'),
        ]
        
        for dir_path in dirs_to_create:
            if dir_path:
                full_path = base_dir / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'paths.data_dir')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_bank_config(self, bank_name: str) -> Optional[Dict[str, Any]]:
        """Get bank-specific configuration.
        
        Args:
            bank_name: Name of the bank
        
        Returns:
            Bank configuration or None if not found
        """
        banks = self.get('banks', {})
        
        # Try exact match first
        for key, config in banks.items():
            if config.get('name', '').lower() == bank_name.lower():
                return config
        
        # Try key match
        bank_key = bank_name.lower().replace(' ', '_').replace('-', '_')
        return banks.get(bank_key)
    
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return self.config_path.parent.parent