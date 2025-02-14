from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ActivityTableLogic:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_activities(self, user_id: int, period: str = "Dia") -> list:
        """
        Busca atividades do usuário baseado no período usando start_time e updated_at
        period: "Dia", "Semana", "Mês" ou "Ano"
        """
        try:
            logger.debug(f"[FILTER] Buscando atividades - Período: {period}")
            
            query = """
                SELECT 
                    id,
                    description,
                    atividade,
                    DATE_FORMAT(start_time, '%d/%m/%Y %H:%i') as start_time,
                    DATE_FORMAT(end_time, '%d/%m/%Y %H:%i') as end_time,
                    DATE_FORMAT(updated_at, '%d/%m/%Y %H:%i') as updated_at,
                    COALESCE(time_exceeded, '00:00:00') as time_exceeded,
                    COALESCE(total_time, '00:00:00') as total_time,
                    CASE
                        WHEN concluido THEN 'Concluído'
                        WHEN pausado THEN 'Pausado'
                        WHEN ativo THEN 'Ativo'
                        ELSE 'Inativo'
                    END as status,
                    COALESCE(ativo, FALSE) as ativo,
                    COALESCE(pausado, FALSE) as pausado,
                    COALESCE(concluido, FALSE) as concluido
                FROM atividades
                WHERE user_id = %s
            """

            params = [user_id]
            
            if period == "Dia":
                query += """ AND (
                    DATE(start_time) = CURRENT_DATE() OR 
                    DATE(updated_at) = CURRENT_DATE()
                )"""
            elif period == "Semana":
                query += """ AND (
                    YEARWEEK(start_time, 1) = YEARWEEK(CURRENT_DATE(), 1) OR
                    YEARWEEK(updated_at, 1) = YEARWEEK(CURRENT_DATE(), 1)
                )"""
            elif period == "Mês":
                query += " AND YEAR(start_time) = YEAR(CURRENT_DATE()) AND MONTH(start_time) = MONTH(CURRENT_DATE())"
            elif period == "Ano":
                query += " AND YEAR(start_time) = YEAR(CURRENT_DATE())"
                
            query += """
                ORDER BY 
                    CASE 
                        WHEN ativo = TRUE THEN 1
                        WHEN pausado = TRUE THEN 2
                        WHEN concluido = TRUE THEN 3
                        ELSE 4
                    END,
                    CASE 
                        WHEN DATE(updated_at) = CURRENT_DATE() THEN updated_at
                        ELSE start_time
                    END DESC
            """

            #logger.debug(f"[FILTER] Query final: {query}")
            results = self.db.execute_query(query, tuple(params))
            #logger.debug(f"[FILTER] Resultados encontrados: {len(results) if results else 0}")
            
            formatted_results = []
            for activity in results:
                try:
                    formatted_activity = {
                        'id': activity['id'],
                        'description': activity['description'],
                        'atividade': activity['atividade'],
                        'start_time': activity['start_time'],
                        'end_time': activity['end_time'],
                        'updated_at': activity['updated_at'],
                        'time_exceeded': activity['time_exceeded'],
                        'total_time': self._format_total_time(activity['total_time']),
                        'status': activity['status'],
                        'ativo': bool(activity['ativo']),
                        'pausado': bool(activity['pausado']),
                        'concluido': bool(activity['concluido'])
                    }
                    formatted_results.append(formatted_activity)
                except Exception as e:
                    logger.error(f"[FILTER] Erro ao formatar atividade {activity.get('id')}: {e}")
                    continue

            return formatted_results
            
        except Exception as e:
            logger.error(f"[FILTER] Erro ao buscar atividades: {e}")
            return []

    def _format_total_time(self, time_value) -> str:
        """
        Formata o tempo total para exibição.
        Aceita timedelta, string HH:MM:SS ou segundos
        """
        try:
            if not time_value:
                return "00:00:00"

            # Se já for timedelta
            if isinstance(time_value, timedelta):
                total_seconds = int(time_value.total_seconds())
            
            # Se for string no formato HH:MM:SS
            elif isinstance(time_value, str) and ":" in time_value:
                try:
                    hours, minutes, seconds = map(int, time_value.split(":"))
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                except ValueError:
                    logger.warning(f"Formato de tempo inválido: {time_value}")
                    return "00:00:00"
            
            # Se for número (segundos)
            else:
                try:
                    total_seconds = int(float(str(time_value)))
                except (ValueError, TypeError):
                    logger.warning(f"Valor de tempo inválido: {time_value}")
                    return "00:00:00"

            # Calcula horas, minutos e segundos
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except Exception as e:
            logger.error(f"Erro ao formatar tempo: {e}")
            return "00:00:00"