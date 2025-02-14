from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DashboardQuery:
    """Classe para consultas específicas do dashboard"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_dashboard_data(self, user_id=None, team_id=None, period='week'):
        """
        Obtém dados para o dashboard
        
        Args:
            user_id: ID do usuário (opcional)
            team_id: ID da equipe (opcional)
            period: Período de análise ('week', 'month', 'semester', 'year')
        """
        try:
            # Definir período de análise
            date_ranges = self._get_date_ranges(period)
            
            data = {
                'indicadores': {},
                'atrasos': {}
            }
            
            # Buscar dados para cada período
            for period_name, date_range in date_ranges.items():
                # Calcular indicadores de tempo
                time_data = self._get_time_indicators(
                    start_date=date_range['start'],
                    end_date=date_range['end'],
                    user_id=user_id,
                    team_id=team_id
                )
                data['indicadores'][period_name] = time_data
            
            # Buscar dados de atrasos
            data['atrasos'] = self._get_delay_data(
                start_date=date_ranges['current']['start'],
                end_date=date_ranges['current']['end'],
                user_id=user_id,
                team_id=team_id
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados do dashboard: {e}")
            return None
    
    def _get_date_ranges(self, period='week'):
        """Define os intervalos de datas para análise"""
        today = datetime.now()
        
        if period == 'week':
            current_start = today - timedelta(days=today.weekday())
            previous_start = current_start - timedelta(weeks=1)
            semester_start = today - timedelta(days=180)
            year_start = today - timedelta(days=365)
        else:
            # Implementar outros períodos conforme necessário
            pass
        
        return {
            'previous': {
                'start': previous_start,
                'end': current_start - timedelta(days=1)
            },
            'current': {
                'start': current_start,
                'end': today
            },
            'semester': {
                'start': semester_start,
                'end': today
            },
            'year': {
                'start': year_start,
                'end': today
            }
        }
    
    def _get_time_indicators(self, start_date, end_date, user_id=None, team_id=None):
        """Calcula indicadores de tempo para o período"""
        try:
            where_clauses = ["a.start_time BETWEEN %s AND %s"]
            params = [start_date, end_date]
            
            if user_id:
                where_clauses.append("a.user_id = %s")
                params.append(user_id)
            elif team_id:
                where_clauses.append("u.equipe_id = %s")
                params.append(team_id)
            
            query = f"""
                SELECT 
                    COUNT(a.id) as total_atividades,
                    SUM(TIME_TO_SEC(a.total_time)) as tempo_total,
                    SUM(TIME_TO_SEC(a.time_exceeded)) as tempo_excedido,
                    COUNT(CASE WHEN a.time_exceeded > '00:00:00' THEN 1 END) as atividades_atrasadas
                FROM atividades a
                JOIN usuarios u ON a.user_id = u.id
                WHERE {' AND '.join(where_clauses)}
            """
            
            result = self.db.execute_query(query, params)
            
            if result and result[0]:
                data = result[0]
                total_atividades = data['total_atividades'] or 0
                tempo_total = data['tempo_total'] or 0
                tempo_excedido = data['tempo_excedido'] or 0
                atividades_atrasadas = data['atividades_atrasadas'] or 0
                
                # Calcular porcentagem de eficiência
                if tempo_total > 0:
                    eficiencia = ((tempo_total - tempo_excedido) / tempo_total) * 100
                else:
                    eficiencia = 100
                
                return {
                    'eficiencia': round(eficiencia, 2),
                    'total_atividades': total_atividades,
                    'atividades_atrasadas': atividades_atrasadas
                }
            
            return {'eficiencia': 100, 'total_atividades': 0, 'atividades_atrasadas': 0}
            
        except Exception as e:
            logger.error(f"Erro ao calcular indicadores de tempo: {e}")
            return {'eficiencia': 0, 'total_atividades': 0, 'atividades_atrasadas': 0}
    
    def _get_delay_data(self, start_date, end_date, user_id=None, team_id=None):
        """Obtém dados de atrasos agrupados por motivo e período"""
        try:
            # Definir períodos de análise
            date_ranges = self._get_date_ranges()
            
            # Dados base para cada período
            periodos = {
                'semana_anterior': date_ranges['previous'],
                'semana_atual': date_ranges['current'],
                'semestral': date_ranges['semester'],
                'anual': date_ranges['year']
            }
            
            atrasos_por_periodo = {}
            
            def converter_tempo_para_segundos(tempo_str):
                """Converte uma string de tempo (incluindo dias) para segundos"""
                try:
                    # Se contém dias
                    if 'day' in tempo_str:
                        # Separar dias da parte de tempo
                        dias_parte, tempo_parte = tempo_str.split(', ')
                        dias = int(dias_parte.split()[0])  # Extrai o número de dias
                        # Converter dias para segundos e adicionar ao tempo
                        segundos_dias = dias * 24 * 3600
                        
                        # Converter a parte do tempo (HH:MM:SS)
                        horas, minutos, segundos = map(int, tempo_parte.split(':'))
                        return segundos_dias + horas * 3600 + minutos * 60 + segundos
                    else:
                        # Formato normal HH:MM:SS
                        horas, minutos, segundos = map(int, tempo_str.split(':'))
                        return horas * 3600 + minutos * 60 + segundos
                except Exception as e:
                    logger.error(f"Erro ao converter tempo '{tempo_str}': {e}")
                    return 0

            # Para cada período, buscar os dados
            for periodo_nome, datas in periodos.items():
                where_clauses = [
                    "a.time_exceeded > '00:00:00'",  # Apenas atividades com atraso
                    "a.reason IS NOT NULL AND a.reason != ''",  # Apenas atividades com motivo preenchido
                    "DATE(a.updated_at) BETWEEN DATE(%s) AND DATE(%s)"  # Filtro por período
                ]
                params = [datas['start'], datas['end']]
                
                if user_id:
                    where_clauses.append("a.user_id = %s")
                    params.append(user_id)
                elif team_id:
                    where_clauses.append("u.equipe_id = %s")
                    params.append(team_id)
                
                query = f"""
                    SELECT 
                        a.reason,
                        COUNT(DISTINCT a.id) as quantidade,
                        SEC_TO_TIME(SUM(TIME_TO_SEC(a.time_exceeded))) as tempo_total,
                        CASE 
                            WHEN SUM(TIME_TO_SEC(a.time_exceeded)) > 14400 THEN 'Alto'
                            WHEN SUM(TIME_TO_SEC(a.time_exceeded)) > 7200 THEN 'Médio'
                            ELSE 'Baixo'
                        END as impacto
                    FROM atividades a
                    JOIN usuarios u ON a.user_id = u.id
                    WHERE {' AND '.join(where_clauses)}
                    GROUP BY a.reason
                    ORDER BY quantidade DESC
                    LIMIT 5
                """
                
                logger.debug(f"Query de atrasos para {periodo_nome}: {query}")
                logger.debug(f"Parâmetros: {params}")
                
                result = self.db.execute_query(query, params)
                
                atrasos = {}
                for row in result:
                    # Usar a nova função para converter o tempo
                    tempo_total_seconds = converter_tempo_para_segundos(str(row['tempo_total']))
                    dias_atraso = round(tempo_total_seconds / (24 * 3600)) or 1
                    
                    atrasos[row['reason']] = {
                        'quantidade': row['quantidade'],
                        'tempo': dias_atraso,
                        'impacto': row['impacto']
                    }
                
                atrasos_por_periodo[periodo_nome] = atrasos
            
            return atrasos_por_periodo
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados de atrasos: {e}")
            return {}
