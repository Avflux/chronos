from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BaseValueObserver:
    """Observer para monitorar mudanças no valor base"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._observers: List = []
        self._base_value: float = 0.0
        
    def attach(self, observer) -> None:
        """Adiciona um novo observer"""
        self._observers.append(observer)
        
    def detach(self, observer) -> None:
        """Remove um observer"""
        self._observers.remove(observer)
        
    def notify(self) -> None:
        """Notifica todos os observers sobre mudança no valor base"""
        for observer in self._observers:
            observer.update_base_value(self._base_value)
            
    def get_base_value(self, user_id: int) -> float:
        """Busca o valor base atual do usuário no banco"""
        try:
            query = """
                SELECT base_value 
                FROM usuarios 
                WHERE id = %(user_id)s
            """
            result = self.db.execute_query(query, {'user_id': user_id})
            if result and result[0]['base_value'] is not None:
                self._base_value = float(result[0]['base_value'])
            else:
                self._base_value = 0.0
                
            self.notify()
            return self._base_value
            
        except Exception as e:
            logger.error(f"[BASE_VALUE] Erro ao buscar valor base: {str(e)}")
            return 0.0
            
    def calculate_final_value(self, total_hours: float, base_days: int = 21, daily_hours: float = 8.8) -> Dict:
        """Calcula o valor final baseado nas horas trabalhadas
        
        Args:
            total_hours: Total de horas trabalhadas em decimal
            base_days: Dias base de trabalho (padrão: 21)
            daily_hours: Horas diárias base em decimal (padrão: 8.8)
            
        Returns:
            Dict contendo os valores calculados
        """
        try:
            # Cálculo do valor total (valor base × total de horas)
            total_value = self._base_value * total_hours
            
            # Cálculo da base de divisão (dias base × horas diárias)
            division_base = base_days * daily_hours
            
            # Cálculo do valor final
            final_value = total_value / division_base if division_base > 0 else 0
            
            return {
                'base_value': self._base_value,
                'total_hours': total_hours,
                'base_days': base_days,
                'daily_hours': daily_hours,
                'total_value': total_value,
                'division_base': division_base,
                'final_value': final_value
            }
            
        except Exception as e:
            logger.error(f"[BASE_VALUE] Erro ao calcular valor final: {str(e)}")
            return {
                'base_value': 0,
                'total_hours': 0,
                'base_days': 0,
                'daily_hours': 0,
                'total_value': 0,
                'division_base': 0,
                'final_value': 0
            }
