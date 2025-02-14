from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TimeController:
    def __init__(self, activity_info=None):
        self.activity_info = activity_info
        self.is_timer_mode = True  # True para timer, False para cronômetro
        self.is_running = False
        self.start_time = None
        self.pause_start_time = None
        self.accumulated_time = timedelta()
        self.total_paused_time = timedelta()
        self.total_elapsed_time = timedelta()  # Novo: para controlar o tempo total decorrido

        # Calcular tempo inicial se houver informações da atividade
        if activity_info:
            self.initial_timer_value = self.calculate_initial_time()
            self.timer_value = self.initial_timer_value
   
            # Se houver tempo total registrado, usar como tempo acumulado
            if 'total_time' in activity_info and activity_info['total_time']:
                try:
                    h, m, s = map(int, activity_info['total_time'].split(':'))
                    self.accumulated_time = timedelta(hours=h, minutes=m, seconds=s)
                    self.total_elapsed_time = self.accumulated_time  # Inicializa tempo total
                except:
                    self.accumulated_time = timedelta()
                    self.total_elapsed_time = timedelta()
        else:
            self.initial_timer_value = timedelta()
            self.timer_value = timedelta()

    def calculate_initial_time(self):
        """Calcula o tempo total entre início e fim previstos"""
        try:
            start_time = self.activity_info['start_time']
            end_time = self.activity_info['end_time']
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%d/%m/%Y %H:%M')         
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%d/%m/%Y %H:%M')
            return end_time - start_time
        except Exception as e:
            logger.error(f"Erro ao calcular tempo inicial: {e}")
            return timedelta()

    def start(self):
        """Inicia ou continua o timer"""
        if not self.is_running:
            current_time = datetime.now()
            if not self.start_time:
                # Primeira inicialização
                self.start_time = current_time
            elif self.pause_start_time:
                # Retomando de uma pausa, adiciona o tempo pausado ao total
                pause_duration = current_time - self.pause_start_time
                self.total_paused_time += pause_duration
                self.pause_start_time = None
            self.is_running = True
            logger.debug("Timer iniciado/resumido")

    def pause(self):
        """Pausa o timer"""
        if self.is_running:
            self.pause_start_time = datetime.now()
            self.is_running = False
            self.accumulated_time = self.get_current_duration()
            # Atualizar tempo total quando pausar
            self.total_elapsed_time = self.get_total_elapsed_time()
            logger.debug(f"Timer pausado. Tempo acumulado: {self.accumulated_time}")

    def update(self):
        """Atualiza e retorna o tempo formatado para o timer principal"""
        if not self.is_running:
            return self.format_time()
        current_time = datetime.now()
        if self.start_time:
            elapsed = current_time - self.start_time - self.total_paused_time
            if self.is_timer_mode:
                self.timer_value = self.initial_timer_value - elapsed
                # Verifica transição para cronômetro
                if self.timer_value <= timedelta():
                    self.is_timer_mode = False
                    self.chronometer_start = current_time  # Marca o início da contagem progressiva
                    self.timer_value = timedelta()  # Começa do zero
            else:
                # Calcula tempo desde que iniciou a contagem progressiva
                self.timer_value = current_time - self.chronometer_start

            # Atualizar tempo total decorrido
            self.total_elapsed_time = self.get_total_elapsed_time()

        return self.format_time()

    def get_total_elapsed_time(self):
        """Calcula o tempo total decorrido desde o início"""
        if not self.start_time:
            return self.accumulated_time

        current_time = datetime.now()
        total_elapsed = current_time - self.start_time - self.total_paused_time
        return total_elapsed + self.accumulated_time

    def format_time(self):
        """Formata o tempo do timer principal para exibição"""
        total_seconds = int(self.timer_value.total_seconds())
        hours = abs(total_seconds) // 3600
        minutes = (abs(total_seconds) % 3600) // 60
        seconds = abs(total_seconds) % 60
        sign = '' if self.is_timer_mode else '+'
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"

    def format_total_time(self):
        """Formata o tempo total decorrido para exibição"""
        total_seconds = int(self.total_elapsed_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_current_duration(self):
        """Retorna a duração atual total"""
        if not self.start_time:
            return self.accumulated_time
        
        current_time = datetime.now()
        return current_time - self.start_time - self.total_paused_time

    def get_formatted_total_time(self):
        """Retorna o tempo total formatado para persistência"""
        return self.format_total_time()

    def set_accumulated_time(self, time_str):
        """Define o tempo acumulado a partir de uma string HH:MM:SS"""
        try:
            h, m, s = map(int, time_str.split(':'))
            self.accumulated_time = timedelta(hours=h, minutes=m, seconds=s)
            self.total_elapsed_time = self.accumulated_time
            logger.debug(f"Tempo acumulado definido: {self.accumulated_time}")
        except Exception as e:
            logger.error(f"Erro ao definir tempo acumulado: {e}")

    def is_time_exceeded(self):
        """Verifica se o tempo foi excedido"""
        return not self.is_timer_mode

    def stop(self):
        """Para o timer completamente"""
        self.is_running = False
        self.pause_start_time = None
        # Atualizar tempo total final
        if self.start_time:
            self.total_elapsed_time = self.get_total_elapsed_time()
        self.start_time = None