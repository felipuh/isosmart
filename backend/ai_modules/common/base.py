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
        # Usar 'ai_module' en lugar de 'module' para evitar conflicto
        log_entry = {
            'ai_module': self.module_name,  # Cambiado de 'module' a 'ai_module'
            'operation': operation,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        # Crear mensaje de log sin usar 'extra' para evitar conflictos
        log_message = f"{self.module_name} - {operation} - {status}"
        if details:
            log_message += f" - {details}"
        
        if status == 'success':
            self.logger.info(log_message)
        elif status == 'error':
            self.logger.error(log_message)
        else:
            self.logger.warning(log_message)
        
        return log_entry
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Valida que los campos requeridos estén presentes"""
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.logger.error(f"Missing required fields: {missing_fields}")
            return False
        
        return True