import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime, time
import logging
import os, sys
from PIL import Image
from ..logic.activity_controls_logic import ActivityControlsLogic
from .activity_form import ActivityForm
from app.core.time.time_manager import TimeManager, timedelta, Optional, Dict
from app.core.time.time_observer import TimeObserver
from app.ui.notifications.notification_manager import NotificationManager
from app.ui.dialogs.break_end_dialog import BreakEndDialog
from app.ui.dialogs.break_start_dialog import BreakStartDialog
from app.ui.dialogs.company_end_dialog import CompanyEndDialog
from app.ui.dialogs.company_end_warning_dialog import CompanyEndWarningDialog
from app.ui.dialogs.time_exceeded_dialog import TimeExceededDialog
from app.utils.tooltip import ToolTip

logger = logging.getLogger(__name__)

class ActivityControls(ctk.CTkFrame, TimeObserver):
    def __init__(self, parent, user_data, db, on_activity_action,
                 active_label=None, selected_label=None):
        super().__init__(parent)
        self.logic = ActivityControlsLogic(db)
        self.db = db
        self.user_data = user_data
        self.on_activity_action = on_activity_action
        self.active_activity_label = active_label
        self.selected_activity_label = selected_label
        self.active_activity = None
        self.selected_activity = None
        self.main_window = self.winfo_toplevel()
        self.bind('<Destroy>', self.on_destroy)

        # Inicializar gerenciadores de tempo
        self.time_manager = TimeManager()
        self.time_manager.add_observer(self)
        self.daily_time_manager = getattr(self.main_window, 'daily_time_manager', None)

        # Inicializar a data do último check
        self._last_check_date = datetime.now().date()

        # Carregar os ícones
        self.load_icons()

        self.setup_ui()
        self.check_current_status()
        self.notification_system = NotificationManager()
        self.notification_system.initialize(self.master, self.user_data['nome'])

        # Adicionar variável de controle para os diálogos
        self._break_end_dialog = None
        self._break_start_dialog = None
        self._company_end_dialog = None
        self._company_end_warning_dialog = None
        self._time_exceeded_dialog = None
        
        # Controle de diálogos já exibidos no dia
        self._dialogs_shown_today = {
            'break_start': None,  # Timestamp da última exibição
            'break_end': None,
            'company_end': None,
            'company_end_warning': None
        }
        
        # Flags para controle de criação de diálogos
        self._creating_dialog = {
            'break_start': False,
            'break_end': False,
            'company_end': False,
            'company_end_warning': False
        }
        
    def load_icons(self):
        """Carrega os ícones dos botões"""
        try:
            if hasattr(sys, "_MEIPASS"):
                icons_dir = os.path.join(sys._MEIPASS, 'icons')
            else:
                icons_dir = os.path.join(os.path.abspath("."), 'icons')

            self.icons = {}
            icon_files = {
                'excel': 'excel_exportar.png'
            }

            for key, filename in icon_files.items():
                image_path = os.path.join(icons_dir, filename)
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    self.icons[key] = ctk.CTkImage(
                        light_image=image, dark_image=image, size=(32, 32)
                    )
                else:
                    logger.warning(f"Ícone não encontrado: {image_path}")
                    self.icons[key] = None
        except Exception as e:
            logger.error(f"Erro ao carregar ícones: {e}")
            self.icons = {}

    def setup_ui(self):
        main_control_frame = ctk.CTkFrame(self)
        main_control_frame.pack(fill="x", padx=5, pady=5)

        button_frame = ctk.CTkFrame(main_control_frame)
        button_frame.pack(side="left", padx=5)

        buttons = [
            ("Criar", "Criar uma nova atividade"),
            ("Pausar", "Pausar uma atividade ativa"),
            ("Continuar", "Continuar uma atividade pausada"),
            ("Concluir", "Concluir uma atividade selecionada")
        ]

        # No loop de criação:
        for text, tooltip_text in buttons:
            btn = ctk.CTkButton(
                button_frame,
                text=text,
                fg_color="#FF5722",
                hover_color="#CE461B",
                command=lambda cmd=text.lower(): self.on_activity_action(cmd),
                state="normal" if text == "Criar" else "disabled",
                width=100,
                height=32
            )
            btn.pack(side="left", padx=5)
            setattr(self, f"btn_{text.lower()}", btn)
            ToolTip(btn, tooltip_text)

        # Keep the Excel button with its icon
        daily_frame = ctk.CTkFrame(main_control_frame)
        daily_frame.pack(side="right", padx=5)

        self.btn_daily = ctk.CTkButton(
            daily_frame,
            text="",
            image=self.icons.get('excel'),
            fg_color="#FF5722",
            hover_color="#CE461B",
            command=self.handle_daily_conclusion,
            width=32,
            height=32
        )
        self.btn_daily.pack(padx=5)
        
        # Adicionar tooltip
        ToolTip(self.btn_daily, "Salvar em sua planilha de horas")

        self.progress_frame = ctk.CTkFrame(main_control_frame)
        self.progress_frame.pack(side="right", padx=10)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="", font=("Roboto", 10))
        self.progress_label.pack(pady=(0, 2))
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, width=200, height=10, fg_color="#333333", progress_color="#FF5722"
        )
        self.progress_bar.pack(pady=(0, 5))
        self.progress_frame.pack_forget()
        self.progress_bar.set(0)

        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(filter_frame, text="Filtrar por:").pack(side="left", padx=5)
        self.period_var = ctk.StringVar(value="Dia")
        self.period_combo = ctk.CTkOptionMenu(
            filter_frame,
            values=["Dia", "Semana", "Mês", "Ano"],
            variable=self.period_var,
            command=self.on_period_change,
            width=120,
            fg_color="#FF5722",
            button_color="#FF5722",
            button_hover_color="#CE461B"
        )
        self.period_combo.pack(side="left", padx=5)
        
        
    def update_button_states(self, force_state=None):
        """Atualiza estado dos botões considerando bloqueio"""
        try:
            if not self.winfo_exists():
                return

            # Verificar horário e bloqueio
            current_time = datetime.now()
            current_date = current_time.date()
            current_timestamp = current_time.timestamp()
            time_now = current_time.time()
            company_end = TimeManager.get_time_object(TimeManager.COMPANY_END_TIME)
            break_start = TimeManager.get_time_object(TimeManager.BREAK_START_TIME)
            break_end = TimeManager.get_time_object(TimeManager.BREAK_END_TIME)
            
            # Garantir que _last_check_date está inicializado
            if not hasattr(self, '_last_check_date'):
                self._last_check_date = current_date
            
            # Resetar controle de diálogos à meia-noite
            if current_date != self._last_check_date:
                self._dialogs_shown_today = {
                    'break_start': None,
                    'break_end': None,
                    'company_end': None,
                    'company_end_warning': None
                }
                self._last_check_date = current_date
            
            # Verificar se é exatamente o horário de início do intervalo
            if (time_now.hour == break_start.hour and 
                time_now.minute == break_start.minute):
                # Verificar se já foi mostrado no último minuto
                last_shown = self._dialogs_shown_today['break_start']
                if last_shown is None or current_timestamp - last_shown >= 60:
                    try:
                        self._create_dialog_safely('break_start', BreakStartDialog)
                    except Exception as e:
                        logger.error(f"Erro ao mostrar diálogo de início de intervalo: {e}")

            # Verificar se é exatamente o horário de fim do intervalo
            if (time_now.hour == break_end.hour and 
                time_now.minute == break_end.minute):
                # Verificar se já foi mostrado no último minuto
                last_shown = self._dialogs_shown_today['break_end']
                if last_shown is None or current_timestamp - last_shown >= 60:
                    try:
                        self._create_dialog_safely('break_end', BreakEndDialog)
                    except Exception as e:
                        logger.error(f"Erro ao mostrar diálogo de fim de intervalo: {e}")

            # Verificar se é 1 minuto antes do fim do expediente
            warning_time = (company_end.hour * 60 + company_end.minute - 1)
            current_minutes = time_now.hour * 60 + time_now.minute
            if current_minutes == warning_time:
                # Verificar se já foi mostrado no último minuto
                last_shown = self._dialogs_shown_today['company_end_warning']
                if last_shown is None or current_timestamp - last_shown >= 60:
                    try:
                        self._create_dialog_safely('company_end_warning', CompanyEndWarningDialog)
                    except Exception as e:
                        logger.error(f"Erro ao mostrar diálogo de aviso de fim de expediente: {e}")

            # Verificar se é exatamente o horário de fim do expediente
            if (time_now.hour == company_end.hour and 
                time_now.minute == company_end.minute):
                # Verificar se já foi mostrado no último minuto
                last_shown = self._dialogs_shown_today['company_end']
                if last_shown is None or current_timestamp - last_shown >= 60:
                    try:
                        self._create_dialog_safely('company_end', CompanyEndDialog)
                    except Exception as e:
                        logger.error(f"Erro ao mostrar diálogo de fim de expediente: {e}")
            
            # Bloqueia se for depois do expediente OU horário de almoço (e não estiver desbloqueado)
            is_blocked = (
                (time_now >= company_end or break_start <= time_now <= break_end)
            )

            # Se estiver bloqueado, desabilita todos os botões e pausa atividade ativa
            if is_blocked:
                logger.debug("Botões bloqueados - Fora do horário comercial ou horário de almoço")
                
                # Pausar atividade ativa se existir
                if self.active_activity:
                    logger.debug("Pausando atividade ativa devido ao bloqueio de horário")
                    self.time_manager.pause_activity()
                    self.logic.update_activity_status(self.active_activity['id'], 'pausado')
                    self.check_current_status()
                    self.refresh_activities()
                
                for button_name in ['criar', 'pausar', 'continuar', 'concluir']:
                    button = getattr(self, f"btn_{button_name}", None)
                    if button and button.winfo_exists():
                        button.configure(state="disabled", fg_color="gray")
                return

            if not self.winfo_exists():  # Verifica se o widget ainda existe
                return
                
            # Estados padrão
            states = {
                'criar': True,
                'pausar': False,
                'continuar': False,
                'concluir': False
            }
            
            # Verificar se há atividade ativa
            states['criar'] = not bool(self.active_activity)
            
            # Se tem atividade selecionada
            if self.selected_activity and self.winfo_exists():
                # Obter status da atividade selecionada
                selected_status = self.selected_activity.get('status', '').upper()
                
                # Regras para Pausar
                if (self.active_activity and 
                    self.active_activity['id'] == self.selected_activity['id'] and
                    selected_status == 'ATIVO'):
                    states['pausar'] = True
                    
                # Regras para Continuar
                if selected_status == 'PAUSADO':
                    states['continuar'] = True
                    
                # Regras para Concluir
                if selected_status in ['ATIVO', 'PAUSADO']:
                    states['concluir'] = True
            
            # Atualizar botões - adicionar verificação de existência
            for button_name, enabled in states.items():
                button_attr = f"btn_{button_name}"
                if hasattr(self, button_attr):
                    button = getattr(self, button_attr)
                    if button.winfo_exists():  # Verifica se o botão ainda existe
                        button.configure(
                            state="normal" if enabled else "disabled",
                            fg_color="#FF5722" if enabled else "gray"
                        )
                        
        except Exception as e:
            logger.error(f"Erro ao atualizar estado dos botões: {e}")

    def _create_dialog_safely(self, dialog_key, dialog_class):
        """Cria um diálogo de forma segura sem travar a interface"""
        # Se já está criando este diálogo, retorna
        if self._creating_dialog[dialog_key]:
            return False
            
        dialog_var = f"_{dialog_key}_dialog"
        current_dialog = getattr(self, dialog_var)
        
        # Se o diálogo não existe ou foi destruído
        if not current_dialog or not current_dialog.winfo_exists():
            # Marca que está criando
            self._creating_dialog[dialog_key] = True
            try:
                # Criar novo diálogo
                new_dialog = dialog_class()  # Não passa mais o parent
                setattr(self, dialog_var, new_dialog)
                # Atualizar timestamp
                current_time = datetime.now().timestamp()
                self._dialogs_shown_today[dialog_key] = current_time
                return True
            finally:
                # Sempre desmarca que está criando
                self._creating_dialog[dialog_key] = False
        return False

    def handle_daily_conclusion(self):        
        """Gerencia o processo de conclusão diária"""
        try:
            # Verifica se existe atividade ativa
            if self.active_activity:
                # Pausa a atividade atual
                self.time_manager.pause_activity()
                
                # Atualiza o status no banco para pausado
                self.logic.update_activity_status(self.active_activity['id'], 'pausado')
                
                # Notifica o usuário
                messagebox.showinfo(
                    "Atividade Pausada",
                    f"A atividade '{self.active_activity['atividade']}' estava em progresso e foi pausada para contabilização do tempo."
                )
                
                # Atualiza a interface
                self.check_current_status()
                self.refresh_activities()

            excel_path = self.get_excel_path()
            if not self.winfo_exists():
                return
            
            if not excel_path or not os.path.exists(excel_path):
                excel_path = self.choose_excel_file()
                if not excel_path:
                    return
                
            excel_path = self.get_excel_path()
            
            if not excel_path or not os.path.exists(excel_path):
                excel_path = self.choose_excel_file()
                if not excel_path:
                    return

            from ....utils.excel_processor import ExcelProcessor
            processor = ExcelProcessor()

            # Mostra o frame de progresso
            self.progress_frame.pack(side="right", padx=10)
            self.progress_bar.set(0)
            
            def log_callback(message):
                logger.info(message)
                self.progress_label.configure(text=message)
                
            def progress_callback(current, total):
                progress = current / total if total > 0 else 0
                self.progress_bar.set(progress)
                self.progress_label.configure(text=f"Processando... {int(progress * 100)}%")
                self.update()  # Força atualização da interface
            
            processor.set_callbacks(log_callback, progress_callback)
            
            success = processor.process_activities_to_excel(
                self.user_data['id'],
                excel_path
            )

            # Aguarda um momento para mostrar 100%
            self.progress_bar.set(1)
            self.progress_label.configure(text="Processamento concluído!")
            self.after(1500, lambda: self.progress_frame.pack_forget())
            
            if success:
                messagebox.showinfo("Sucesso", "Atividades exportadas com sucesso!")
            else:
                messagebox.showerror("Erro", "Erro ao exportar atividades")
            
        except Exception as e:
            logger.error(f"Erro ao processar conclusão diária: {e}")
            messagebox.showerror("Erro", f"Erro ao processar conclusão diária: {e}")
            self.progress_frame.pack_forget()

    def choose_excel_file(self):
        """Permite ao usuário escolher o arquivo Excel de destino"""
        try:
            file_path = filedialog.askopenfilename(
                title="Selecione o arquivo Excel",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if file_path:
                self.save_excel_path(file_path)
                return file_path
            return None
            
        except Exception as e:
            logger.error(f"Erro ao selecionar arquivo Excel: {e}")
            messagebox.showerror("Erro", "Erro ao selecionar arquivo Excel")
            return None

    def get_excel_path(self):
        """Recupera o caminho do Excel da conclusão diária do config.txt"""
        try:
            if os.path.exists("config.txt"):
                with open("config.txt", "r") as f:
                    for line in f:
                        if line.startswith("DAILY_EXCEL_PATH="):
                            return line.split("=")[1].strip()
            return None
                
        except Exception as e:
            logger.error(f"Erro ao ler caminho do Excel: {e}")
            return None

    def save_excel_path(self, path):
        """Salva o caminho do Excel da conclusão diária no config.txt"""
        try:
            existing_content = []
            if os.path.exists("config.txt"):
                with open("config.txt", "r") as f:
                    existing_content = f.readlines()

            # Remove linha existente com DAILY_EXCEL_PATH se houver
            existing_content = [line for line in existing_content 
                            if not line.startswith("DAILY_EXCEL_PATH=")]

            # Adiciona novo caminho
            existing_content.append(f"DAILY_EXCEL_PATH={path}\n")

            # Salva arquivo mantendo outras linhas
            with open("config.txt", "w") as f:
                f.writelines(existing_content)
                    
        except PermissionError as e:
            logger.error(f"Erro de permissão: {e}")
            messagebox.showerror("Erro", "Por favor, feche o arquivo Excel antes de continuar.")
        except Exception as e:
            logger.error(f"Erro ao salvar caminho do Excel: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar caminho do Excel: {e}")

    def update_daily_time(self, daily_time: timedelta) -> None:
        """Atualiza o display do tempo diário e decimal"""
        try:
            total_seconds = int(daily_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            # Atualizar o label de tempo em HH:MM:SS
            self.daily_hours_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Converter para decimal e atualizar o label
            decimal_hours = self._convert_to_decimal_hours(daily_time)
            self.decimal_hours_label.configure(text=f"{decimal_hours:.3f}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar display do tempo diário: {e}")

    def update_timer_display(self, timer_value: timedelta, total_time: timedelta) -> None:
        # Delegar para a janela principal
        if self.main_window:
            self.main_window.update_timer_display(timer_value, total_time)

    def update_activity_status(self, activity_info: Optional[Dict]) -> None:
        # Atualizar estados dos botões baseado no novo status
        self.check_current_status()

    def notify_time_exceeded(self, activity_info: Dict) -> None:
        """Atualiza a interface quando o tempo é excedido"""
        try:
            if activity_info and 'id' in activity_info:
                # Verificar se o tempo realmente foi excedido
                query = """
                    SELECT time_exceeded
                    FROM atividades 
                    WHERE id = %s
                """
                result = self.db.execute_query(query, (activity_info['id'],))
                
                if result and result[0]['time_exceeded'] != '00:00:00':
                    # Atualizar o status no banco apenas se o tempo foi realmente excedido
                    update_query = """
                        UPDATE atividades 
                        SET time_exceeded = TRUE 
                        WHERE id = %s
                    """
                    self.db.execute_query(update_query, (activity_info['id'],))
                    
                    # Atualizar a interface
                    self.refresh_activities()
                    logger.debug(f"Status de tempo excedido atualizado para atividade {activity_info['id']}")

                    # Mostrar diálogo de tempo excedido se ainda não estiver aberto
                    if not self._time_exceeded_dialog or not self._time_exceeded_dialog.winfo_exists():
                        self._time_exceeded_dialog = TimeExceededDialog(self, activity_info.get('atividade'))
                
        except Exception as e:
            logger.error(f"Erro ao processar tempo excedido: {e}")

    def check_current_status(self):
        """Verifica e atualiza status atual"""
        try:
            query = """
                SELECT id, description, atividade, start_time, end_time, 
                       ativo, pausado, concluido
                FROM atividades 
                WHERE user_id = %s
                AND ativo = TRUE 
                AND concluido = FALSE
                AND pausado = FALSE
                LIMIT 1
            """
            result = self.logic.db.execute_query(query, (self.user_data['id'],))
            if result and result[0]:
                activity = result[0]
                self.active_activity = activity
                if self.active_activity_label:
                    self.active_activity_label.configure(
                        text=f"Atividade atual (ATIVA): {activity['atividade']}"
                    )
            else:
                self.active_activity = None
                if self.active_activity_label:
                    self.active_activity_label.configure(text="Atividade atual: Nenhuma")
            self.update_button_states()
        except Exception as e:
            logger.error(f"Erro ao verificar status atual: {e}")
            if self.active_activity_label:
                self.active_activity_label.configure(text="Atividade atual: Erro ao carregar")
            self.active_activity = None

    def clear_selection(self, event=None):
        """Limpa a seleção atual"""
        try:
            if self.winfo_exists() and hasattr(self, 'selected_activity_label'):
                self.selected_activity = None
                if self.selected_activity_label.winfo_exists():
                    self.selected_activity_label.configure(text="Atividade selecionada: Nenhuma")
                self.update_button_states()
        except Exception as e:
            logger.error(f"Erro ao limpar seleção: {e}")

    def on_destroy(self, event=None):
        """Limpa referências quando o widget for destruído"""
        try:
            if event.widget == self:
                self.active_activity = None
                self.selected_activity = None
        except Exception as e:
            logger.error(f"Erro ao limpar referências: {e}")

    def on_activity_selected(self, activity):
        """Manipula seleção de atividade na tabela"""
        try:
            self.selected_activity = activity
            if activity and self.selected_activity_label:
                status = activity.get('status', '').upper()
                self.selected_activity_label.configure(
                    text=f"Atividade selecionada ({status}): {activity['atividade']}"
                )
                
                # Atualiza o display do tempo total com o valor do banco
                if activity.get('total_time'):
                    self.time_manager.state.total_elapsed_time = self.time_manager.formatter.parse_time_str(activity['total_time'])
                    self.notify_observers_timer(self.time_manager.state.timer_value, self.time_manager.state.total_elapsed_time)
                
            elif self.selected_activity_label:
                self.selected_activity_label.configure(text="Atividade selecionada: Nenhuma")
                
            # Atualizar estados dos botões
            self.update_button_states()
            
        except Exception as e:
            logger.error(f"Erro ao selecionar atividade: {e}")

    def check_if_blocked(self) -> bool:
        """Verifica se as ações estão bloqueadas"""
        try:
            current_time = datetime.now().time()
            company_end = TimeManager.get_time_object(TimeManager.COMPANY_END_TIME)
            break_start = TimeManager.get_time_object(TimeManager.BREAK_START_TIME)
            break_end = TimeManager.get_time_object(TimeManager.BREAK_END_TIME)
            
            is_blocked = (
                (current_time >= company_end or break_start <= current_time <= break_end)
            )
            
            if is_blocked:
                messagebox.showwarning(
                    "Acesso Bloqueado",
                    "Ações bloqueadas fora do horário comercial ou durante o intervalo."
                )
            return is_blocked
        except Exception as e:
            logger.error(f"Erro ao verificar bloqueio: {e}")
            return True  # Em caso de erro, bloqueia por segurança

    def handle_activity_action(self, action):
        """Manipula ações de atividade"""
        try:
            if self.check_if_blocked():
                return
                
            if not self.winfo_exists():
                return
                
            # Verificar primeiro se é criar
            if action == "criar":
                logger.debug("[BOTÃO] Tentando criar atividade")
                if not self.active_activity:
                    # Verificar horário comercial antes de criar
                    current_time = datetime.now().time()
                    break_start = TimeManager.get_time_object(TimeManager.BREAK_START_TIME)
                    break_end = TimeManager.get_time_object(TimeManager.BREAK_END_TIME)
                    
                    if break_start <= current_time <= break_end:
                        if not messagebox.askyesno(
                            "Horário de Intervalo",
                            f"Você está no horário de intervalo ({break_start.strftime('%H:%M')} - {break_end.strftime('%H:%M')}).\n"
                            "Deseja continuar mesmo assim?"
                        ):
                            return
                            
                    # Zerar os labels de tempo antes de criar nova atividade
                    if hasattr(self.main_window, 'timer_label'):
                        self.main_window.timer_label.configure(text="00:00:00")
                    if hasattr(self.main_window, 'total_time_label'):
                        self.main_window.total_time_label.configure(text="Total: 00:00:00")
                    
                    self.show_activity_form()
                    
                    # Iniciar daily_time_manager se ainda não estiver rodando
                    if not self.daily_time_manager.is_running:
                        self.daily_time_manager.start_daily_timer()
                else:
                    messagebox.showwarning("Aviso", "Você já possui uma atividade em andamento!")
                    logger.warning("[BOTÃO] Tentativa de criar com atividade ativa existente")
                return
            
            # Depois verificar seleção para outras ações
            if not self.selected_activity:
                logger.warning("[BOTÃO] Tentativa de ação sem atividade selecionada")
                messagebox.showwarning("Aviso", "Selecione uma atividade primeiro!")
                return
            
            # Confirmação do usuário
            if not messagebox.askyesno("Confirmar", f"Deseja realmente {action} esta atividade?"):
                logger.debug("[BOTÃO] Ação cancelada pelo usuário")
                return
                
            # Verificar tempo excedido antes de concluir
            if action == "concluir":
                logger.debug("[CONTROLS] Verificando tempo excedido antes de concluir")
                if not self.time_manager.handle_time_exceeded(self.master, self.selected_activity):
                    logger.debug("[CONTROLS] Conclusão cancelada - tempo excedido requer justificativa")
                    return
                    
            # Verifica se há outra atividade ativa
            if self.active_activity and self.active_activity['id'] != self.selected_activity['id']:
                # Primeiro pausar a atividade atual
                logger.debug("[BOTÃO] Pausando atividade atual antes de continuar outra")
                current_active_id = self.active_activity['id']
                self.time_manager.pause_activity()
                
                # Atualizar status da atividade atual para pausado
                self.logic.update_activity_status(current_active_id, 'pausado')
                
            # Iniciar daily_time se ainda não estiver rodando
            if self.daily_time_manager and not self.daily_time_manager.is_running:
                self.daily_time_manager.start_daily_timer()
                
            # Verifica se a atividade selecionada é a ativa atualmente
            is_selected_active = (
                self.active_activity and 
                self.selected_activity and 
                self.active_activity['id'] == self.selected_activity['id']
            )
            
            # Mapeamento de ações para status
            status_mapping = {
                "continuar": "ativo",
                "pausar": "pausado",
                "concluir": "concluido"
            }
            new_status = status_mapping.get(action)
            
            if not new_status:
                logger.error(f"[BOTÃO] Status não mapeado para ação: {action}")
                return
            
            # Atualizar status da atividade selecionada
            logger.debug(f"[BOTÃO] Atualizando status para: {new_status}")
            success, message = self.logic.update_activity_status(
                self.selected_activity['id'], 
                new_status
            )
            
            if success:
                # Tratar ações pós atualização de status
                if action == "continuar":
                    logger.debug("[TIMER] Iniciando timer da atividade")
                    self.time_manager.resume_activity(self.selected_activity)
                elif action == "pausar" and is_selected_active:
                    logger.debug("[TIMER] Pausando timer da atividade")
                    self.time_manager.pause_activity()
                elif action == "concluir" and is_selected_active:
                    logger.debug("[TIMER] Parando timer da atividade")
                    self.time_manager.stop_activity()
                    
                logger.info(f"[BOTÃO] Ação {action} executada com sucesso")
                self.check_current_status()
                self.refresh_activities()
            else:
                logger.error(f"[BOTÃO] Erro na ação {action}: {message}")
                messagebox.showerror("Erro", message)
                
        except Exception as e:
            logger.error(f"[BOTÃO] Erro ao executar ação {action}: {e}")
            if self.winfo_exists():
                messagebox.showerror("Erro", f"Erro ao executar ação: {e}")

    def _has_active_activities(self):
        """Verifica se existem atividades ativas além da atual"""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM atividades 
                WHERE user_id = %s
                AND ativo = TRUE 
                AND concluido = FALSE
                AND pausado = FALSE
            """
            result = self.logic.db.execute_query(query, (self.user_data['id'],))
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            logger.error(f"Erro ao verificar atividades ativas: {e}")
            return False

    def show_activity_form(self):
        """Exibe o formulário de criação de atividade"""
        try:
            # Verificar se não há atividade ativa
            if not self.active_activity:
                # Verificar horário comercial antes de criar
                current_time = datetime.now().time()
                break_start = TimeManager.get_time_object(TimeManager.BREAK_START_TIME)
                break_end = TimeManager.get_time_object(TimeManager.BREAK_END_TIME)
                
                if break_start <= current_time <= break_end:
                    if not messagebox.askyesno(
                        "Horário de Intervalo",
                        f"Você está no horário de intervalo ({break_start.strftime('%H:%M')} - {break_end.strftime('%H:%M')}).\n"
                        "Deseja continuar mesmo assim?"
                    ):
                        return
                        
                # Criar e exibir o formulário de atividade
                activity_form = ActivityForm(
                    self.main_window,  # Passar a janela principal como parent
                    self.user_data,    # Dados do usuário
                    self.on_activity_created  # Callback quando atividade é criada
                )
                activity_form.grab_set()  # Tornar o formulário modal
            else:
                messagebox.showwarning("Aviso", "Você já possui uma atividade em andamento!")
        except Exception as e:
            logger.error(f"Erro ao abrir formulário de atividade: {e}")
            messagebox.showerror(
                "Erro",
                "Não foi possível abrir o formulário de atividade."
            )

    def refresh_activities(self):
        """Atualiza a tabela de atividades"""
        try:
            if hasattr(self.main_window, 'activity_table'):
                self.main_window.activity_table.update_activities()
        except Exception as e:
            logger.error(f"Erro ao atualizar tabela de atividades: {e}")

    def on_activity_created(self, activity_data=None):
        """
        Callback chamado quando uma atividade é criada
        
        Args:
            activity_data (dict, optional): Dados da atividade criada
        """
        try:
            # Limpar seleção atual
            self.clear_selection()
            
            # Atualizar status
            self.check_current_status()
            
            # Atualizar tabela de atividades
            self.refresh_activities()           
            
            # Forçar atualização dos botões
            self.after(100, self.update_button_states)
            
            logger.info(f"Atividade criada e interface atualizada. Dados: {activity_data}")
        except Exception as e:
            logger.error(f"Erro após criar atividade: {e}")
            messagebox.showerror(
                "Erro",
                "Erro ao atualizar interface após criar atividade"
            )

    def update_time_exceeded(self, activity_id):
        """Atualiza o status de tempo excedido no banco de dados"""
        try:
            query = """
                UPDATE atividades 
                SET time_exceeded = TRUE 
                WHERE id = %s
            """
            self.db.execute_query(query, (activity_id,))
            # Atualizar a interface se necessário
            self.refresh_activities()
        except Exception as e:
            logger.error(f"Erro ao atualizar tempo excedido: {e}")

    def on_period_change(self, value):
        """Manipula mudança no filtro de período"""
        try:
            logger.debug(f"[FILTER] Mudando período para: {value}")
            
            # Atualiza a lista de valores do combobox para incluir "Semana"
            self.period_combo.configure(values=["Dia", "Semana", "Mês", "Ano"])
            
            if hasattr(self.main_window, 'activity_table'):
                logger.debug(f"[FILTER] Atualizando tabela com novo período: {value}")
                self.main_window.activity_table.update_activities(filter_period=value)
            else:
                logger.warning("[FILTER] ActivityTable não encontrado")
                
        except Exception as e:
            logger.error(f"[FILTER] Erro ao mudar período: {e}")
            messagebox.showerror("Erro", "Erro ao aplicar filtro")

    def open_on_double_click_activity_form(self, activity_data):
        """Abre o formulário de atividade no duplo clique com verificações adicionais"""
        try:
            # Verificar primeiro se está bloqueado por horário comercial
            if self.check_if_blocked():
                logger.warning("[DUPLO CLIQUE] Tentativa de criar atividade fora do horário comercial")
                return

            # Verificar se já existe atividade ativa
            if self.active_activity:
                messagebox.showwarning("Aviso", "Você já possui uma atividade em andamento!")
                logger.warning("[DUPLO CLIQUE] Tentativa de editar com atividade ativa existente")
                return

            # Verificar horário comercial
            current_time = datetime.now().time()
            break_start = TimeManager.get_time_object(TimeManager.BREAK_START_TIME)
            break_end = TimeManager.get_time_object(TimeManager.BREAK_END_TIME)
            
            if break_start <= current_time <= break_end:
                if not messagebox.askyesno(
                    "Horário de Intervalo",
                    f"Você está no horário de intervalo ({break_start.strftime('%H:%M')} - {break_end.strftime('%H:%M')}).\n"
                    "Deseja continuar mesmo assim?"
                ):
                    return

            # Se passou pelos checks, abrir o formulário
            activity_form = ActivityForm(
                self.main_window,    # Passar a janela principal como parent
                self.user_data,      # Dados do usuário
                self.on_activity_created,  # Callback após criar/editar
                activity_data=activity_data  # Dados da atividade para preencher o formulário
            )
            activity_form.grab_set()  # Tornar o formulário modal

        except Exception as e:
            logger.error(f"Erro ao abrir formulário utilizando o clique duplo: {e}")
            messagebox.showerror(
                "Erro",
                "Não foi possível abrir o formulário utilizando o clique duplo."
            )

    def on_lock_state_changed(self, is_unlocked: bool):
        """Callback chamado quando o estado de bloqueio muda"""
        try:
            # Apenas atualizar os estados dos botões existentes
            self.update_button_states()
            
            # Atualizar labels de atividade
            if self.active_activity and self.active_activity_label:
                self.active_activity_label.configure(
                    text=f"Atividade atual (PAUSADA): {self.active_activity['atividade']}"
                )
            if self.selected_activity and self.selected_activity_label:
                status = self.selected_activity.get('status', '').upper()
                self.selected_activity_label.configure(
                    text=f"Atividade selecionada ({status}): {self.selected_activity['atividade']}"
                )
            
            logger.debug(f"[CONTROLS] Estados atualizados com bloqueio: {is_unlocked}")
            
        except Exception as e:
            logger.error(f"Erro ao processar mudança de bloqueio: {e}")

    def update_idle_status(self, status: str):
        """
        Atualiza o status de ociosidade do usuário.
        
        Args:
            status: 'idle' para inativo, 'active' para ativo
        """
        try:
            if status == 'idle':
                # Lógica para quando o usuário está inativo
                logger.debug("Usuário está inativo (ActivityControls)")
            else:
                # Lógica para quando o usuário retoma a atividade
                logger.debug("Usuário está ativo (ActivityControls)")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status de ociosidade: {e}")

    def _handle_conclude(self):
        """Gerencia a conclusão da atividade"""
        try:
            logger.debug("[CONTROLS] Iniciando processo de conclusão")
            
            if self.active_activity:
                logger.debug(f"[CONTROLS] Verificando tempo excedido para atividade {self.active_activity['id']}")
                
                # Verificar tempo excedido antes de concluir
                if not self.time_manager.handle_time_exceeded(self.master, self.active_activity):
                    logger.debug("[CONTROLS] Conclusão cancelada - tempo excedido requer justificativa")
                    return
                    
                # Se passou pela verificação, atualiza o status
                logger.debug("[CONTROLS] Atualizando status para concluído")
                self.logic.update_activity_status(self.active_activity['id'], 'concluido')
                
        except Exception as e:
            logger.error(f"[CONTROLS] Erro ao concluir atividade: {e}")

# Exportar todas as classes necessárias
__all__ = ['ActivityForm', 'ActivityTable', 'ActivityControls']