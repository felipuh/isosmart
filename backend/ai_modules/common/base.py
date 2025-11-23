import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AIModuleBase(ABC):
    """Clase base para todos los módulos de IA"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.logger = logging.getLogger(f'ai_modules.{module_name}')
        self.created_at = datetime.now()
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Método principal de procesamiento - debe ser implementado"""
        pass
    
    def log_execution(self, operation: str, status: str, details: Dict = None):
        """Log estandarizado de operaciones"""
        log_entry = {
            'module': self.module_name,
            'operation': operation,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        if status == 'success':
            self.logger.info(f"{operation} completed successfully", extra=log_entry)
        elif status == 'error':
            self.logger.error(f"{operation} failed", extra=log_entry)
        else:
            self.logger.warning(f"{operation} - {status}", extra=log_entry)
        
        return log_entry
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Valida que los campos requeridos estén presentes"""
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.logger.error(f"Missing required fields: {missing_fields}")
            return False
        
        return True
