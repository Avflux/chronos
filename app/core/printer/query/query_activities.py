from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class QueryActivities:
    def __init__(self, db_connection):
        self.db = db_connection  # Recebe a conexão do banco
    
    def get_activities_report_data(self, user_id: int, month: int = None, year: int = None) -> Dict:
        """Busca dados das atividades, usuário e equipe para o relatório"""
        try:
            logger.debug(f"[REPORT] Iniciando busca de dados para relatório - Usuário ID: {user_id}")
            
            # Se mês e ano não forem fornecidos, usa o mês atual
            if month is None or year is None:
                current_date = datetime.now()
                month = month or current_date.month
                year = year or current_date.year
            
            # Primeiro, busca informações do usuário
            user_query = """
                SELECT 
                    u.id as user_id,
                    u.nome as user_name,
                    e.nome as team_name,
                    u.base_value
                FROM usuarios u
                JOIN equipes e ON u.equipe_id = e.id
                WHERE u.id = %(user_id)s
            """
            
            user_result = self.db.execute_query(user_query, {'user_id': user_id})
            
            if not user_result:
                logger.warning(f"[REPORT] Usuário não encontrado - ID: {user_id}")
                raise ValueError(f"Usuário com ID {user_id} não encontrado")
            
            user_info = {
                'user_id': user_result[0]['user_id'],
                'user_name': user_result[0]['user_name'],
                'team_name': user_result[0]['team_name'],
                'base_value': float(user_result[0]['base_value'] or 0)
            }
            
            # Agora busca as atividades com filtro de data
            activities_query = """
                SELECT 
                    a.description,
                    a.atividade as activity,
                    COALESCE(a.total_time, '00:00:00') as total_time,
                    a.created_at
                FROM atividades a
                WHERE a.user_id = %(user_id)s
                AND MONTH(a.created_at) = %(month)s
                AND YEAR(a.created_at) = %(year)s
                ORDER BY a.created_at DESC
            """
            
            query_params = {
                'user_id': user_id,
                'month': month,
                'year': year
            }
            
            logger.debug("[REPORT] Executando query de atividades")
            activities_result = self.db.execute_query(activities_query, query_params)
            
            activities = []
            if activities_result:
                for row in activities_result:
                    activities.append({
                        'description': row['description'],
                        'activity': row['activity'],
                        'total_time': row['total_time']
                    })
                logger.info(f"[REPORT] {len(activities)} atividades encontradas para o usuário {user_info['user_name']}")
            else:
                logger.info(f"[REPORT] Nenhuma atividade encontrada para o usuário {user_info['user_name']}")
            
            return {
                'user_info': user_info,
                'activities': activities,
                'period': {
                    'month': month,
                    'year': year
                }
            }
            
        except ValueError as e:
            logger.error(f"[REPORT] {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[REPORT] Erro ao buscar dados para relatório: {str(e)}")
            raise

    def update_user_base_value(self, user_id: int, base_value: float) -> bool:
        """Atualiza o valor base do usuário"""
        try:
            query = """
                UPDATE usuarios
                SET base_value = %(base_value)s
                WHERE id = %(user_id)s
            """
            
            self.db.execute_query(query, {
                'user_id': user_id,
                'base_value': base_value
            })
            
            logger.info(f"[BASE_VALUE] Valor base atualizado para usuário {user_id}: {base_value}")
            return True
            
        except Exception as e:
            logger.error(f"[BASE_VALUE] Erro ao atualizar valor base: {str(e)}")
            return False
