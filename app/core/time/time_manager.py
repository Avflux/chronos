from datetime import datetime, timedelta, time
import logging
import json
from typing import Optional, Dict
from plyer import notification
import os
from .time_state import TimeState
from .time_observer import TimeObservable, TimeObserver
from ...database.connection import DatabaseConnection
from ...config.settings import APP_CONFIG
from .lock_observer import LockStateObserver
from ..idleness.idle_detector import IdleDetector
from ...ui.dialogs.reason_exceeded_dialog import ReasonExceededDialog
from .time_exceeded_observer import TimeExceededObserver

logger = logging.getLogger(__name__)

class TimeManager(TimeObservable):
    # Constantes de horário comercial
    COMPANY_START_TIME = "08:00:00"
    BREAK_START_TIME = "12:15:00"
    BREAK_END_TIME = "13:15:00"
    COMPANY_END_TIME = "18:30:00"
    APP_ICON = APP_CONFIG['icons']['app']
    _instance = None  # Singleton instance
    
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            super().__init__()  # Importante: chamar o init da classe pai
            self.state = TimeState()
            self.db = DatabaseConnection()
            self._timer_id = None
            self._check_lock_timer_id = None
            self._start_lock_check()
            self.idle_detector = IdleDetector()
            self.idle_detector.add_observer(self)
            self.idle_detector.start()
            self.time_exceeded_observer = TimeExceededObserver()
            self._initialized = True

    def calculate_initial_time(self, start_time, end_time) -> str:
        """
        Calcula o tempo inicial considerando horário comercial
        """
            
    def start_activity(self, activity_info: Dict) -> None:
        try:
            logger.debug(f"[TIMER_DEBUG] Estado inicial do timer")
            logger.debug(f"[TIMER_DEBUG] Modo atual: {self.state.current_mode}")
            logger.debug(f"[TIMER_DEBUG] Timer value: {self.state.timer_value}")
            
            # Resetar o estado antes de iniciar nova atividade
            self.state.reset()
            
            self.state.set_activity_info(activity_info)
            self.state.start_time = datetime.now()
            self.state.is_running = True
            
            # Forçar modo regressivo inicialmente
            self.state.current_mode = 'regressivo'
            
            # Reset de estados
            self.state.time_exceeded_handled = False
            self.state.chronometer_start = None
            
            # Notificar observadores do reset
            self.notify_observers_timer(timedelta(), timedelta())

            query = """
                SELECT time_regress, time_exceeded
                FROM atividades 
                WHERE id = %s
            """
            result = self.db.execute_query(query, (activity_info['id'],))
            
            if result and result[0]:
                time_val = result[0]['time_regress']
                if time_val and time_val != '00:00:00':
                    # Modo regressivo
                    if isinstance(time_val, timedelta):
                        self.state.initial_timer_value = time_val
                    else:
                        h, m, s = map(int, str(time_val).split(':'))
                        self.state.initial_timer_value = timedelta(hours=h, minutes=m, seconds=s)
                    logger.debug(f"[TIMER_DEBUG] Configurado timer regressivo: {self.state.initial_timer_value}")

            self._start_timer_update()

            logger.debug(f"[TIMER_DEBUG] Estado final do timer")
            logger.debug(f"[TIMER_DEBUG] Modo final: {self.state.current_mode}")
            logger.debug(f"[TIMER_DEBUG] Timer value final: {self.state.timer_value}")
            
        except Exception as e:
            logger.error(f"[TIMER] Erro ao iniciar atividade: {e}")
            
    def pause_activity(self) -> None:
        """Pausa a atividade atual"""
        try:
            if self.state.is_running:
                # Cancelar timer existente
                if self._timer_id:
                    for observer in self._observers:
                        if hasattr(observer, 'after_cancel'):
                            observer.after_cancel(self._timer_id)
                            break

                self._timer_id = None
                current_time = datetime.now()
                self.state.pause_start_time = current_time
                self.state.is_running = False

                # Salvar apenas os tempos necessários no banco
                if self.state.activity_info:
                    query = """
                        UPDATE atividades 
                        SET total_time = %s,
                            time_regress = %s,
                            time_exceeded = %s,
                            current_mode = %s
                        WHERE id = %s
                    """
                    
                    total_time = self.format_total_time(self.state.total_elapsed_time)
                    
                    # Determinar valores baseado no modo atual
                    if self.state.current_mode == 'regressivo':
                        time_regress = self.format_total_time(self.state.timer_value)
                        time_exceeded = '00:00:00'
                    else:
                        time_regress = '00:00:00'
                        time_exceeded = self.format_total_time(abs(self.state.timer_value))
                    
                    params = (
                        total_time,
                        time_regress, 
                        time_exceeded,
                        self.state.current_mode,
                        self.state.activity_info['id']
                    )
                    self.db.execute_query(query, params)
                    
        except Exception as e:
            logger.error(f"Erro ao pausar atividade: {e}")

    def _save_exact_state(self):
        """Salva o estado com precisão total"""
        state_data = {
            'mode': self.state.current_mode,
            'timer_value': self.format_total_time(self.state.timer_value),
            'total_time': self.format_total_time(self.state.total_elapsed_time),
            'start_time': self.state.start_time.isoformat() if self.state.start_time else None,
            'accumulated_time': self.format_total_time(self.state.accumulated_time)
        }
        
        self._save_to_db(state_data)

    def _save_to_db(self):
        """Salva o estado atual no banco de dados"""
        try:
            if not self.state.activity_info:
                return

            current_time = datetime.now()
            total_time = self.format_total_time(self.state.total_elapsed_time)
            
            # Determinar valores baseado no modo atual
            if self.state.current_mode == 'regressivo':
                time_regress = self.format_total_time(self.state.timer_value)
                time_exceeded = '00:00:00'
            else:
                time_regress = '00:00:00'
                time_exceeded = self.format_total_time(abs(self.state.timer_value))

            query = """
                UPDATE atividades 
                SET total_time = %s,
                    time_regress = %s,
                    time_exceeded = %s
                WHERE id = %s
            """
            
            params = (total_time, time_regress, time_exceeded, self.state.activity_info['id'])
            self.db.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Erro ao salvar estado no banco: {e}")
            
    def resume_activity(self, activity_info: Dict) -> None:
        """Retoma uma atividade pausada"""
        try:
            if not self.state.is_running:
                self.state.activity_info = activity_info
                query = """
                    SELECT time_regress, time_exceeded, total_time, current_mode
                    FROM atividades 
                    WHERE id = %s
                """
                result = self.db.execute_query(query, (activity_info['id'],))
                
                if result:
                    saved_data = result[0]
                    logger.debug(f"[TIMER_RESUME] Dados recuperados do banco: {saved_data}")
                    
                    # Restaurar modo
                    self.state.current_mode = saved_data['current_mode'] or 'regressivo'
                    
                    # Restaurar tempo total
                    if saved_data['total_time']:
                        # Verificar se já é timedelta
                        if isinstance(saved_data['total_time'], timedelta):
                            self.state.total_elapsed_time = saved_data['total_time']
                        else:
                            self.state.total_elapsed_time = self.parse_time(saved_data['total_time'])
                        self.state.accumulated_time = int(self.state.total_elapsed_time.total_seconds())
                    
                    # Configurar timer baseado no modo
                    if self.state.current_mode == 'regressivo':
                        # Verificar se já é timedelta
                        if isinstance(saved_data['time_regress'], timedelta):
                            self.state.timer_value = saved_data['time_regress']
                        else:
                            self.state.timer_value = self.parse_time(saved_data['time_regress'])
                        self.state.initial_timer_value = self.state.timer_value
                        self.state.chronometer_start = None
                    else:  # modo progressivo
                        # Verificar se já é timedelta
                        if isinstance(saved_data['time_exceeded'], timedelta):
                            exceeded_time = saved_data['time_exceeded']
                        else:
                            exceeded_time = self.parse_time(saved_data['time_exceeded'])
                        # Configure o chronometer_start para manter o tempo excedido
                        self.state.chronometer_start = datetime.now() - exceeded_time
                    
                    logger.debug(f"[TIMER_RESUME] Valores restaurados:")
                    logger.debug(f"  - Timer Value: {self.state.timer_value}")
                    logger.debug(f"  - Total Time: {self.state.total_elapsed_time}")
                    logger.debug(f"  - Mode: {self.state.current_mode}")
                    
                    self.state.start_time = datetime.now()
                    self.state.is_running = True
                    self._start_timer_update()
                
                else:
                    raise Exception("Dados da atividade não encontrados no banco")
                
        except Exception as e:
            logger.error(f"Erro ao retomar atividade: {e}")
            
    def stop_activity(self, parent_window=None, activity_info=None):
        """Para a atividade atual"""
        try:
            if activity_info and parent_window:
                if not self.handle_time_exceeded(parent_window, activity_info):
                    return False
                
            if self._timer_id:
                self.state.is_running = False
                
                # Atualizar todos os tempos no banco
                if self.state.activity_info:
                    query = """
                        UPDATE atividades 
                        SET total_time = %s,
                            time_regress = %s,
                            time_exceeded = %s
                        WHERE id = %s
                    """
                    
                    # Formatar tempos para salvar
                    total_time = self.format_total_time(self.state.total_elapsed_time)
                    
                    # Determinar valores finais baseado no modo atual
                    if self.state.current_mode == 'regressivo':
                        time_regress = self.format_total_time(self.state.timer_value)
                        time_exceeded = '00:00:00'
                    else:
                        time_regress = '00:00:00'
                        time_exceeded = self.format_total_time(abs(self.state.timer_value))
                    
                    params = (total_time, time_regress, time_exceeded, self.state.activity_info['id'])
                    self.db.execute_query(query, params)
                
                self.state.reset()
                logger.info("Atividade parada")
                self.notify_observers_activity(None)
                
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar atividade: {e}")
            return False
            
    def _start_timer_update(self) -> None:
        """Inicia o loop de atualização do timer"""
        try:
            if not self.state.is_running:
                return

            self._update_timer()
            
            # Agenda próxima atualização usando o loop de eventos do Tkinter
            for observer in self._observers:
                if hasattr(observer, 'after'):
                    self._timer_id = observer.after(1000, self._start_timer_update)
                    break
                    
        except Exception as e:
            logger.error(f"Erro no loop de atualização: {e}")
            
    def _update_timer(self) -> None:
        try:
            if not self.state.is_running:
                return
                    
            logger.debug("[TIMER_DEBUG] ---- Iniciando atualização do timer ----")
            current_time = datetime.now()
            elapsed = current_time - self.state.start_time - self.state.total_paused_time
            logger.debug(f"[TIMER_DEBUG] Tempo decorrido: {elapsed}")

            # Adicionar atributo last_save se não existir
            if not hasattr(self.state, 'last_save'):
                self.state.last_save = current_time

            # Verificar se passou 1 minuto desde o último salvamento
            if (current_time - self.state.last_save).total_seconds() >= 60:
                logger.debug("[TIMER_DEBUG] Salvando dados periódicos no banco")
                
                query = """
                    UPDATE atividades 
                    SET total_time = %s,
                        time_exceeded = %s
                    WHERE id = %s
                """
                
                total_time = self.format_total_time(self.state.total_elapsed_time)
                time_exceeded = '00:00:00'
                
                if self.state.current_mode == 'progressivo':
                    time_exceeded = self.format_total_time(abs(self.state.timer_value))
                
                self.db.execute_query(
                    query,
                    (total_time, time_exceeded, self.state.activity_info['id'])
                )
                
                # Atualizar timestamp do último salvamento
                self.state.last_save = current_time
                logger.debug(f"[TIMER_DEBUG] Dados salvos - total_time: {total_time}, time_exceeded: {time_exceeded}")

            if self.state.current_mode == 'regressivo':
                self.state.timer_value = self.state.initial_timer_value - elapsed
                logger.debug(f"[TIMER_DEBUG] Valor timer regressivo: {self.state.timer_value}")
                
                if self.state.timer_value.total_seconds() <= 0:
                    logger.debug("[MODE_CHANGE] Mudando para modo progressivo")
                    logger.debug(f"[MODE_CHANGE] Último valor regressivo: {self.state.timer_value}")
                    self.state.current_mode = 'progressivo'
                    self.state.chronometer_start = current_time
                    self.state.timer_value = timedelta(seconds=1)
                    logger.debug(f"[MODE_CHANGE] Primeiro valor progressivo: {self.state.timer_value}")
                    
                    # Atualizar banco e enviar notificação
                    self._update_mode_in_db('progressivo')
                    self._send_time_exceeded_notification()
                    
                    # Notificar observers sem mensagem
                    self.notify_time_exceeded(self.state.activity_info)
                    
            else:
                if self.state.chronometer_start is None:
                    self.state.chronometer_start = current_time
                self.state.timer_value = current_time - self.state.chronometer_start
                logger.debug(f"[TIMER_DEBUG] Valor timer progressivo: {self.state.timer_value}")
            
            self.state.total_elapsed_time = self._get_current_duration()
            logger.debug(f"[TIMER_DEBUG] Tempo total acumulado: {self.state.total_elapsed_time}")
            logger.debug("[TIMER_DEBUG] ---- Fim da atualização ----")

            # Notificar observadores sobre as mudanças
            self.notify_observers_timer(self.state.timer_value, self.state.total_elapsed_time)

        except Exception as e:
            logger.error(f"[TIMER] Erro ao atualizar timer: {e}")

    def _send_time_exceeded_notification(self):
        """Envia notificação do sistema quando o tempo é excedido"""
        try:
            if not self.state.activity_info:
                return
                
            # Preparar mensagem
            activity_name = self.state.activity_info.get('atividade', 'Atividade')
            message = f"O tempo da atividade '{activity_name}' foi excedido!"
            
            # Obter e verificar caminho do ícone
            icon = APP_CONFIG['icons']['time_exceeded']

            logger.debug(f"[NOTIFICATION] Caminho do ícone: {icon}")
            logger.debug(f"[NOTIFICATION] Ícone existe? {os.path.exists(icon)}")
            logger.debug(f"[NOTIFICATION] Caminho absoluto: {os.path.abspath(icon)}")
            
            # Enviar notificação do sistema
            notification.notify(
                title='Tempo Excedido',
                message=message,
                app_icon=os.path.abspath(icon) if os.path.exists(icon) else None,
                timeout=10,
                toast=True
            )
            
            logger.debug(f"[NOTIFICATION] Notificação enviada para atividade: {activity_name}")
            
        except Exception as e:
            logger.error(f"[NOTIFICATION] Erro ao enviar notificação: {e}")

    def _update_mode_in_db(self, mode: str):
        """Atualiza modo no banco"""
        logger.debug(f"[DB_UPDATE] ---- Atualizando modo para: {mode} ----")
        query = """
            UPDATE atividades
            SET time_regress = %s
            WHERE id = %s
        """
        time_regress = '00:00:00' if mode == 'progressivo' else '00:00:01'
        logger.debug(f"[DB_UPDATE] Valores a serem salvos: regress={time_regress}")
        
        self.db.execute_query(query, (time_regress, self.state.activity_info['id']))
        logger.debug("[DB_UPDATE] ---- Atualização concluída ----")

    def _save_current_state_to_db(self):
        """Salva estado atual no banco de forma consistente"""
        try:
            # Salva o estado completo como JSON para restauração precisa
            state_data = {
                'mode': self.state.current_mode,
                'timer_value': self.format_total_time(self.state.timer_value),
                'total_time': self.format_total_time(self.state.total_elapsed_time),
                'start_time': self.state.start_time.isoformat() if self.state.start_time else None,
                'accumulated_time': self.format_total_time(self.state.accumulated_time)
            }

            # Calcula valores para salvar baseado no modo atual
            total_time = self.format_total_time(self.state.total_elapsed_time)
            
            if self.state.current_mode == 'regressivo':
                time_regress = self.format_total_time(self.state.timer_value)
                time_exceeded = '00:00:00'
            else:
                time_regress = '00:00:00' 
                time_exceeded = self.format_total_time(abs(self.state.timer_value))

            query = """
                UPDATE atividades 
                SET total_time = %s,
                    time_regress = %s,
                    time_exceeded = %s,
                    current_mode = %s,
                    last_state = %s
                WHERE id = %s
            """

            # Salva o estado completo como JSON para restauração precisa
            state_data = {
                'mode': self.state.current_mode,
                'timer_value': self.format_total_time(self.state.timer_value),
                'total_time': self.format_total_time(self.state.total_elapsed_time),
                'start_time': self.state.start_time.isoformat() if self.state.start_time else None,
                'accumulated_time': self.format_total_time(self.state.accumulated_time)
            }

            logger.debug("[DB_SAVE] Valores calculados para salvar:")
            logger.debug(f"  - total_time: {total_time}")
            logger.debug(f"  - time_regress: {time_regress}")
            logger.debug(f"  - time_exceeded: {time_exceeded}")
            logger.debug(f"  - state_data: {state_data}")

            self.db.execute_query(query, (
                total_time,
                time_regress, 
                time_exceeded,
                self.state.current_mode,
                json.dumps(state_data),
                self.state.activity_info['id']
            ))

            logger.debug("[DB_SAVE] ---- Estado salvo com sucesso ----")

        except Exception as e:
            logger.error(f"[DB_SAVE] Erro ao salvar estado: {e}")
            raise

    def _restore_state(self, saved_state: dict) -> None:
        with self.state._state_lock:  # Usar lock para thread safety
            self.state.current_mode = saved_state['mode']
            self.state.timer_value = self.parse_time(saved_state['timer_value'])
            self.state.total_elapsed_time = self.parse_time(saved_state['total_time'])
            
            if saved_state['start_time']:
                self.state.start_time = datetime.fromisoformat(saved_state['start_time'])
                
            # Manter acumuladores precisos
            self.state.accumulated_time = self.parse_time(saved_state['accumulated_time'])
            
            logger.debug(f"Estado restaurado com sucesso: {self.state.timer_value}")

    def _load_state_from_db(self):
        """Carrega estado do banco"""
        logger.debug("[DB_LOAD] ---- Iniciando carregamento do banco ----")
        query = """
            SELECT time_regress, time_exceeded, total_time, current_mode
            FROM atividades 
            WHERE id = %s
        """
        result = self.db.execute_query(query, (self.state.activity_info['id'],))
        logger.debug(f"[DB_LOAD] Dados recuperados: {result[0] if result else None}")
        logger.debug("[DB_LOAD] ---- Fim do carregamento ----")
        return result[0] if result else None
    
    def _restore_state(self, saved_state):
        """Restaura estado salvo"""
        logger.debug("[STATE_RESTORE] ---- Iniciando restauração ----")
        logger.debug("[STATE_RESTORE] Estado recuperado do banco:")
        logger.debug(f"  - Modo: {saved_state['current_mode']}")
        logger.debug(f"  - Time Regress: {saved_state['time_regress']}")
        logger.debug(f"  - Time Exceeded: {saved_state['time_exceeded']}")
        logger.debug(f"  - Total Time: {saved_state['total_time']}")

        self.state.current_mode = saved_state['current_mode']
        
        if saved_state['time_regress'] != '00:00:00':
            h, m, s = map(int, saved_state['time_regress'].split(':'))
            self.state.initial_timer_value = timedelta(hours=h, minutes=m, seconds=s)
            self.state.chronometer_start = None
            logger.debug(f"[STATE_RESTORE] Timer regressivo restaurado: {self.state.initial_timer_value}")
        else:
            h, m, s = map(int, saved_state['time_exceeded'].split(':'))
            self.state.chronometer_start = datetime.now() - timedelta(hours=h, minutes=m, seconds=s)
            logger.debug(f"[STATE_RESTORE] Timer progressivo restaurado: {self.state.chronometer_start}")

        if saved_state['total_time']:
            h, m, s = map(int, saved_state['total_time'].split(':'))
            self.state.accumulated_time = timedelta(hours=h, minutes=m, seconds=s)
            logger.debug(f"[STATE_RESTORE] Tempo acumulado restaurado: {self.state.accumulated_time}")

        logger.debug("[STATE_RESTORE] ---- Restauração finalizada ----")

    def _handle_time_exceeded(self) -> None:
        """Manipula o evento de tempo excedido"""
        try:
            if not self.state.activity_info:
                return
                    
            # Atualizar modo do timer
            self.state.current_mode = 'progressivo'
            
            # Atualizar status no banco
            query = """
                UPDATE atividades 
                SET time_regress = '00:00:00',
                    time_exceeded = CASE
                        WHEN NOW() > end_time THEN TIMEDIFF(NOW(), end_time)
                        ELSE '00:00:00'
                    END
                WHERE id = %s
            """
            self.db.execute_query(query, (self.state.activity_info['id'],))
            
            try:
                notification.notify(
                    title='Tempo Excedido',
                    message=f"O tempo da atividade '{self.state.activity_info['atividade']}' foi excedido!",
                    app_icon=self.APP_ICON,
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Erro ao enviar notificação: {e}")
                
            logger.debug("Evento de tempo excedido manipulado")
            
        except Exception as e:
            logger.error(f"Erro ao manipular tempo excedido: {e}")

    def _get_current_duration(self) -> timedelta:
        """Calcula a duração atual total"""
        if not self.state.start_time:
            # Converter accumulated_time (segundos) para timedelta
            return timedelta(seconds=self.state.accumulated_time)
            
        current_duration = datetime.now() - self.state.start_time - self.state.total_paused_time
        # Converter accumulated_time para timedelta antes de somar
        return current_duration + timedelta(seconds=self.state.accumulated_time)
        
    def _update_activity_time(self) -> None:
        """Atualiza o tempo total da atividade no banco de dados"""
        try:
            if not self.state.activity_info:
                return
                
            total_time = self.format_total_time(self.state.total_elapsed_time)
            
            query = """
                UPDATE atividades 
                SET total_time = %s
                WHERE id = %s
            """
            self.db.execute_query(
                query,
                (total_time, self.state.activity_info['id'])
            )
            
            logger.debug(f"Tempo atualizado: {total_time}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar tempo da atividade: {e}")
            
            
    def _update_time_exceeded(self) -> None:
        """Atualiza o status de tempo excedido no banco de dados"""
        try:
            if not self.state.activity_info:
                return
                
            query = """
                UPDATE atividades 
                SET time_exceeded = CASE
                    WHEN NOW() > end_time THEN TIMEDIFF(NOW(), end_time)
                    ELSE '00:00:00'
                END
                WHERE id = %s
            """
            self.db.execute_query(query, (self.state.activity_info['id'],))
            
            logger.debug("Status de tempo excedido atualizado")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status de tempo excedido: {e}")

    @staticmethod
    def check_company_hours():
        """Verifica o horário atual em relação aos horários da empresa"""
        now = datetime.now().time()
        start_time = datetime.strptime(TimeManager.COMPANY_START_TIME, "%H:%M:%S").time()
        break_start = datetime.strptime(TimeManager.BREAK_START_TIME, "%H:%M:%S").time()
        break_end = datetime.strptime(TimeManager.BREAK_END_TIME, "%H:%M:%S").time()
        end_time = datetime.strptime(TimeManager.COMPANY_END_TIME, "%H:%M:%S").time()
        
        if now < start_time:
            return "before_hours"
        elif break_start <= now <= break_end:
            return "break_time"
        elif now > end_time:
            return "after_hours"
        return "working_hours"
    
    @staticmethod
    def should_compute_time(current_status):
        """Verifica se deve computar o tempo baseado no status da empresa"""
        if current_status == "before_hours":
            return False, "Horário anterior ao início das atividades da empresa"
        elif current_status == "break_time":
            return False, "Horário de intervalo"
        elif current_status == "after_hours":
            return False, "Horário posterior ao encerramento das atividades"
        return True, None

    @staticmethod
    def check_activity_status(activity):
        """Verifica o status atual de uma atividade"""
        now = datetime.now()
        
        if not activity['end_time']:
            return 'em_andamento'
        elif activity['total_time']:
            return 'concluida'
        elif activity['end_time'] < now and activity['time_exceeded']:
            return 'tempo_excedido'
        else:
            return 'pausada'

    @staticmethod
    def calculate_total_time(start_time, end_time, breaks=None):
        """Calcula o tempo total considerando intervalos"""
        total = end_time - start_time
        
        if breaks:
            for break_start, break_end in breaks:
                break_duration = break_end - break_start
                total -= break_duration
                
        return total

    @staticmethod
    def calculate_business_hours_duration(start: datetime, end: datetime) -> timedelta:
        """
        Calcula a duração dentro do horário comercial, descontando o intervalo de almoço.
        Um dia completo de trabalho tem 9 horas (das 8:00 às 18:00, menos 1 hora de almoço).
        """
        if start >= end:
            return timedelta()

        # Ajustar para horário comercial
        day_start = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.COMPANY_START_TIME))  # 08:00
        if start < day_start:
            start = day_start

        day_end = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.COMPANY_END_TIME))    # 18:00
        if end > day_end:
            end = day_end

        # Horários de almoço
        break_start = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.BREAK_START_TIME))    # 12:15
        break_end = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.BREAK_END_TIME))      # 13:15

        # Calcular duração da manhã (08:00-12:15 = 4h15m máximo)
        morning_duration = timedelta()
        if start < break_start:
            morning_end = min(end, break_start)
            morning_duration = morning_end - start

        # Calcular duração da tarde (13:15-18:00 = 4h45m máximo)
        afternoon_duration = timedelta()
        if end > break_end:
            afternoon_start = max(start, break_end)
            afternoon_duration = end - afternoon_start

        # Retornar soma dos períodos
        return morning_duration + afternoon_duration

    @staticmethod
    def format_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
        """
        Calcula e formata a duração entre dois horários considerando horário comercial.
        Cada dia útil tem 9 horas de trabalho (8:00-18:00 menos 1h de almoço).
        """
        if end_time is None:
            end_time = datetime.now()

        total_duration = timedelta()

        # Se os horários são do mesmo dia
        if start_time.date() == end_time.date():
            total_duration = TimeManager.calculate_business_hours_duration(start_time, end_time)
        else:
            # Calcular tempo do primeiro dia
            first_day_end = datetime.combine(start_time.date(), 
                TimeManager.get_time_object(TimeManager.COMPANY_END_TIME))
            total_duration += TimeManager.calculate_business_hours_duration(start_time, first_day_end)

            # Calcular dias completos entre início e fim (cada dia = 9 horas)
            current_date = start_time.date() + timedelta(days=1)
            while current_date < end_time.date():
                day_start = datetime.combine(current_date, 
                    TimeManager.get_time_object(TimeManager.COMPANY_START_TIME))
                day_end = datetime.combine(current_date, 
                    TimeManager.get_time_object(TimeManager.COMPANY_END_TIME))
                total_duration += TimeManager.calculate_business_hours_duration(day_start, day_end)
                current_date += timedelta(days=1)

            # Calcular tempo do último dia se necessário
            if current_date == end_time.date():
                last_day_start = datetime.combine(end_time.date(), 
                    TimeManager.get_time_object(TimeManager.COMPANY_START_TIME))
                total_duration += TimeManager.calculate_business_hours_duration(last_day_start, end_time)

        return TimeManager.format_total_time(total_duration)

    @staticmethod
    def get_time_tuple(time_str):
        """Converte string de tempo em tupla (hora, minuto)"""
        try:
            h, m, s = map(int, time_str.split(':'))
            return (h, m)
        except Exception as e:
            logger.error(f"Erro ao converter tempo para tupla: {e}")
            return (0, 0)
            
    @staticmethod
    def get_time_object(time_str):
        """Converte string de tempo em objeto time"""
        try:
            h, m, s = map(int, time_str.split(':'))
            return time(h, m, s)
        except Exception as e:
            logger.error(f"Erro ao converter tempo para objeto: {e}")
            return time()

    @staticmethod
    def parse_time(time_str: str) -> timedelta:
        """Converte string HH:MM:SS para timedelta"""
        try:
            h, m, s = map(int, time_str.split(':'))
            return timedelta(hours=h, minutes=m, seconds=s)
        except Exception as e:
            logger.error(f"Erro ao converter tempo: {e}")
            return timedelta()

    @staticmethod
    def format_total_time(time_val) -> str:
        """Converte tempo para string HH:MM:SS"""
        if isinstance(time_val, timedelta):
            total_seconds = int(time_val.total_seconds())
        elif isinstance(time_val, int):
            total_seconds = time_val
        else:
            logger.error(f"Tipo de tempo não suportado: {type(time_val)}")
            return "00:00:00"
            
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def calculate_business_hours_duration(start: datetime, end: datetime) -> timedelta:
        """Calcula a duração dentro do horário comercial, descontando o intervalo de almoço"""
        if start >= end:
            return timedelta()

        # Ajustar para horário comercial se necessário
        day_start = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.COMPANY_START_TIME))
        if start < day_start:
            start = day_start

        day_end = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.COMPANY_END_TIME))
        if end > day_end:
            end = day_end
            
        # Se o período é inválido após ajustes
        if start >= end:
            return timedelta()
            
        # Converter horários de almoço para o dia atual
        break_start = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.BREAK_START_TIME))
        break_end = datetime.combine(start.date(), 
            TimeManager.get_time_object(TimeManager.BREAK_END_TIME))
        
        total_duration = timedelta()
        
        # Se o período inclui o horário de almoço
        if start < break_start and end > break_end:
            # Adicionar tempo antes do almoço
            total_duration += break_start - start
            # Adicionar tempo depois do almoço
            total_duration += end - break_end
        elif start < break_start and end > break_start:
            # Período termina durante o almoço
            total_duration += break_start - start
        elif start < break_end and end > break_end:
            # Período começa durante o almoço
            total_duration += end - break_end
        else:
            # Período está totalmente fora do horário de almoço
            if start >= break_end or end <= break_start:
                total_duration += end - start
                
        return total_duration

    @staticmethod
    def format_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
        """Calcula e formata a duração entre dois horários considerando horário comercial"""
        if end_time is None:
            end_time = datetime.now()
            
        total_duration = timedelta()
        
        # Se os horários são do mesmo dia
        if start_time.date() == end_time.date():
            total_duration = TimeManager.calculate_business_hours_duration(start_time, end_time)
        else:
            # Calcular tempo do primeiro dia
            first_day_end = datetime.combine(start_time.date(), 
                TimeManager.get_time_object(TimeManager.COMPANY_END_TIME))
            total_duration += TimeManager.calculate_business_hours_duration(start_time, first_day_end)
            
            # Calcular dias completos entre início e fim
            current_date = start_time.date() + timedelta(days=1)
            while current_date < end_time.date():
                day_start = datetime.combine(current_date, 
                    TimeManager.get_time_object(TimeManager.COMPANY_START_TIME))
                day_end = datetime.combine(current_date, 
                    TimeManager.get_time_object(TimeManager.COMPANY_END_TIME))
                total_duration += TimeManager.calculate_business_hours_duration(day_start, day_end)
                current_date += timedelta(days=1)
            
            # Calcular tempo do último dia se necessário
            if current_date == end_time.date():
                last_day_start = datetime.combine(end_time.date(), 
                    TimeManager.get_time_object(TimeManager.COMPANY_START_TIME))
                total_duration += TimeManager.calculate_business_hours_duration(last_day_start, end_time)
            
        return TimeManager.format_total_time(total_duration)

    def _start_lock_check(self):
        """Inicia verificação periódica do estado de bloqueio"""
        try:
            def check_loop():
                current_time = datetime.now().time()
                company_end = datetime.strptime(self.COMPANY_END_TIME, "%H:%M:%S").time()
                
                # Verificar se acabou de atingir o horário de fim
                if current_time >= company_end:
                    logger.debug("[LOCK] Horário de fim atingido, pausando atividades...")
                    
                    # Verificar se há usuário configurado
                    if hasattr(self.state, 'user_id') and self.state.user_id:
                        query = """
                            SELECT id, atividade 
                            FROM atividades 
                            WHERE user_id = %s
                            AND ativo = TRUE 
                            AND concluido = FALSE
                            AND pausado = FALSE
                        """
                        active_activities = self.db.execute_query(query, (self.state.user_id,))
                        
                        for activity in active_activities:
                            logger.debug(f"[LOCK] Pausando atividade {activity['id']}: {activity['atividade']}")
                            
                            # Primeiro atualizar no banco
                            update_query = """
                                UPDATE atividades 
                                SET pausado = TRUE,
                                    ativo = TRUE,
                                    concluido = FALSE,
                                    total_time = COALESCE(
                                        (SELECT SEC_TO_TIME(
                                            TIME_TO_SEC(TIMEDIFF(NOW(), start_time))
                                        )
                                    ), '00:00:00')
                                WHERE id = %s
                            """
                            self.db.execute_query(update_query, (activity['id'],))
                            
                            # Depois pausar o timer
                            self.pause_activity()
                            
                            # Notificar observadores para atualizar interface
                            self.notify_observers_activity(None)
                            
                        # Notificar mudança de estado de bloqueio
                        self._notify_lock_state()
                        
                        logger.info("[LOCK] Todas as atividades foram pausadas pelo horário de fim")
                
                # Agendar próxima verificação
                for observer in self._observers:
                    if hasattr(observer, 'after'):
                        observer.after(1000, check_loop)  # Verificar a cada segundo, como no update_clock
                        break

            # Iniciar o loop
            check_loop()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar verificação de bloqueio: {e}")

    def _notify_lock_state(self):
        """Notifica observadores sobre estado de bloqueio"""
        try:
            lock_observer = LockStateObserver()
            for observer in self._observers:
                if hasattr(observer, 'user_data'):
                    is_unlocked = lock_observer.check_lock_state(observer.user_data['id'])
                    observer.on_lock_state_changed(is_unlocked)
        except Exception as e:
            logger.error(f"Erro ao notificar estado de bloqueio: {e}")

    def add_observer(self, observer: TimeObserver) -> None:
        """Adiciona um novo observador e verifica estado inicial de bloqueio"""
        super().add_observer(observer)
        
        # Verificar estado inicial de bloqueio
        try:
            if hasattr(observer, 'user_data'):
                lock_observer = LockStateObserver()
                is_unlocked = lock_observer.check_lock_state(observer.user_data['id'])
                if hasattr(observer, 'on_lock_state_changed'):
                    observer.on_lock_state_changed(is_unlocked)
        except Exception as e:
            logger.error(f"Erro ao verificar estado inicial de bloqueio: {e}")

    def handle_time_exceeded(self, parent_window, activity_info: Dict) -> bool:
        """
        Gerencia o diálogo de tempo excedido
        Retorna True se a atividade pode ser concluída, False caso contrário
        """
        try:
            logger.debug(f"[TIME_MANAGER] ---- Iniciando verificação de tempo excedido para atividade {activity_info['id']} ----")
            
            needs_justification = self.time_exceeded_observer.check_activity_state(activity_info['id'])
            logger.debug(f"[TIME_MANAGER] Resultado da verificação: precisa de justificativa? {needs_justification}")
            
            if needs_justification:
                logger.info(f"[TIME_MANAGER] Abrindo diálogo de justificativa")
                
                dialog = ReasonExceededDialog(parent_window, activity_info)
                parent_window.wait_window(dialog)
                
                if dialog.result:
                    reason = dialog.result['selected_reason'] or dialog.result['other_reason']
                    logger.debug(f"[TIME_MANAGER] Justificativa fornecida: {reason}")
                    
                    if reason:
                        update_query = """
                            UPDATE atividades 
                            SET reason = %s,
                                concluido = TRUE,
                                ativo = FALSE,
                                pausado = FALSE
                            WHERE id = %s
                        """
                        logger.debug(f"[TIME_MANAGER] Executando query de atualização: {update_query}")
                        logger.debug(f"[TIME_MANAGER] Parâmetros: reason={reason}, id={activity_info['id']}")
                        
                        self.db.execute_query(update_query, (reason, activity_info['id']))
                        logger.info(f"[TIME_MANAGER] Justificativa salva com sucesso")
                        return True
                        
                    logger.warning(f"[TIME_MANAGER] Justificativa não fornecida")
                    return False
                    
                logger.warning(f"[TIME_MANAGER] Diálogo cancelado")
                return False
                
            logger.debug(f"[TIME_MANAGER] Atividade não precisa de justificativa")
            return True
            
        except Exception as e:
            logger.error(f"[TIME_MANAGER] Erro ao gerenciar tempo excedido: {e}")
            return False
        finally:
            logger.debug("[TIME_MANAGER] ---- Fim da verificação de tempo excedido ----")

    def update_idle_status(self, status):
        if status == 'idle':
            self.handle_idle_time()
        else:
            self.handle_activity_resume()

    def handle_idle_time(self):
        """Inicia o tempo ocioso"""
        logger.info("Iniciando contagem de tempo ocioso")
        if self.state.activity_info:
            logger.info(f"Atividade atual: {self.state.activity_info['atividade']}")

    def handle_activity_resume(self):
        """Quando a atividade é retomada, salva o tempo ocioso acumulado"""
        try:
            idle_time = self.idle_detector.get_accumulated_idle_time()
            if idle_time.total_seconds() > 0:
                logger.info(f"Salvando tempo ocioso: {idle_time}")
                self.save_idle_time_to_db(idle_time)
                self.idle_detector.reset_accumulated_idle_time()
        except Exception as e:
            logger.error(f"Erro ao processar retomada de atividade: {e}")

    def save_idle_time_to_db(self, idle_time: timedelta):
        """Salva o tempo ocioso no banco de dados"""
        try:
            if not self.state.user_id:
                logger.warning("Tentativa de salvar tempo ocioso sem user_id")
                return

            # Buscar tempo ocioso atual
            query = "SELECT ociosidade FROM usuarios WHERE id = %s"
            result = self.db.execute_query(query, (self.state.user_id,))
            
            current_idle_time = timedelta()
            if result and result[0]['ociosidade']:
                h, m, s = map(int, str(result[0]['ociosidade']).split(':'))
                current_idle_time = timedelta(hours=h, minutes=m, seconds=s)

            # Somar tempos
            total_idle_time = current_idle_time + idle_time
            formatted_time = self.format_total_time(total_idle_time)

            # Atualizar banco
            update_query = """
                UPDATE usuarios 
                SET ociosidade = %s
                WHERE id = %s
            """
            self.db.execute_query(update_query, (formatted_time, self.state.user_id))
            logger.info(f"Tempo ocioso atualizado no banco: {formatted_time}")

        except Exception as e:
            logger.error(f"Erro ao salvar tempo ocioso: {e}")

    def cleanup(self):
        self.idle_detector.stop()
        # ... outras limpezas ...

    def set_user(self, user_data):
        """Define o usuário atual"""
        if user_data and 'id' in user_data:
            self.state.set_user_id(user_data['id'])
            logger.info(f"User ID configurado: {user_data['id']}")