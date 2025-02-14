from datetime import datetime
import logging
from ....core.activity.activity_manager import ActivityManager
from ....core.activity.activity_validator import ActivityValidator

logger = logging.getLogger(__name__)

class ActivityControlsLogic:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_active_activity(self, user_id):
        """Busca a atividade ativa do usuário"""
        try:
            query = """
                SELECT * FROM atividades
                WHERE user_id = %s 
                AND ativo = TRUE 
                AND concluido = FALSE
                LIMIT 1
            """
            result = self.db.execute_query(query, (user_id,))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar atividade ativa: {e}")
            return None

    def get_button_states(self, selected_activity=None):
        """
        Determina o estado dos botões baseado na atividade selecionada 
        e na existência de atividade ativa
        """
        # Buscar atividade ativa atual
        active_activity = self.get_active_activity(self.user_id)
        
        # Estados padrão (todos desativados exceto Criar)
        states = {
            'criar': True,
            'pausar': False,
            'continuar': False,
            'concluir': False
        }
        
        # Se existe atividade ativa, desativa o botão criar
        if active_activity:
            states['criar'] = False
            
        # Se tem atividade selecionada
        if selected_activity:
            selected_status = selected_activity.get('status', '').lower()
            
            # Regras para o botão Pausar
            if (active_activity and 
                selected_activity['id'] == active_activity['id'] and
                selected_status == 'ativo'):
                states['pausar'] = True
            
            # Regras para o botão Continuar
            if (selected_status == 'pausado' and
                not active_activity):
                states['continuar'] = True
            
            # Regras para o botão Concluir
            if selected_status in ['ativo', 'pausado']:
                states['concluir'] = True
                
        return states

    def update_activity_status(self, activity_id, new_status):
        """
        Atualiza o status de uma atividade no banco de dados.
        """
        try:
            # Primeiro verificar o status atual da atividade
            status_query = """
                SELECT pausado
                FROM atividades 
                WHERE id = %s
            """
            result = self.db.execute_query(status_query, (activity_id,))
            
            if not result:
                return False, "Atividade não encontrada"
                
            is_paused = result[0]['pausado']
            
            # Se estiver concluindo uma atividade pausada
            if new_status == 'concluido' and is_paused:
                query = """
                    UPDATE atividades
                    SET concluido = TRUE,
                        ativo = FALSE,
                        pausado = FALSE
                    WHERE id = %s
                """
                self.db.execute_query(query, (activity_id,))
                return True, "Atividade concluída com sucesso!"
                
            # Para outros casos, manter a lógica existente
            status_values = {
                'ativo': {'ativo': True, 'pausado': False, 'concluido': False},
                'pausado': {'ativo': False, 'pausado': True, 'concluido': False},
                'concluido': {'ativo': False, 'pausado': False, 'concluido': True}
            }
            
            if new_status not in status_values:
                return False, f"Status inválido: {new_status}"

            values = status_values[new_status]
            query = """
                UPDATE atividades
                SET ativo = %s,
                    pausado = %s,
                    concluido = %s
                WHERE id = %s
            """
            params = (values['ativo'], values['pausado'], values['concluido'], activity_id)
            self.db.execute_query(query, params)
            
            return True, f"Atividade {new_status} com sucesso!"
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status da atividade: {e}")
            return False, f"Erro ao atualizar status: {e}"
        