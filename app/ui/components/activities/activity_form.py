import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, time
import logging
import os, sys
from PIL import Image
from ....database.connection import DatabaseConnection
from ..logic.activity_form_logic import ActivityFormLogic
from ....utils.excel_selector import ExcelSelector
from ....utils.helpers import BaseDialog
from ....utils.tooltip import ToolTip
from ....core.time.time_manager import TimeManager

logger = logging.getLogger(__name__)

class ActivityForm(BaseDialog):

    def __init__(self, parent, user_data, on_activity_created, activity_data=None):
        super().__init__(parent)
        self.activity_data = activity_data
        self.title("Nova Atividade")
        self.logic = ActivityFormLogic(DatabaseConnection())
        self.user_data = user_data
        self.on_activity_created = on_activity_created
        self.time_manager = TimeManager()
        
        if hasattr(sys, "_MEIPASS"):
            icons_dir = os.path.join(sys._MEIPASS, 'icons', 'excel.png')
        else:
            icons_dir = os.path.join(os.path.abspath("."), 'icons', 'excel.png')
        
        # Carregar a imagem do Excel
        try:
            excel_image = Image.open(icons_dir)
            self.excel_icon = ctk.CTkImage(light_image=excel_image, dark_image=excel_image, size=(32, 32))
        except Exception as e:
            logger.error(f"Erro ao carregar ícone do Excel: {e}")
            self.excel_icon = None

        window_width = 500
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width/2) - (window_width/2))
        y = int((screen_height/2) - (window_height/2))
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.setup_ui()
                # Depois, se houver dados de atividade, preencher
        if self.activity_data:
            self.populate_form_fields()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=35, pady=25)

        self.create_form_field(main_frame, "Criado por:", disabled_value=self.user_data['name_id'])

        desc_label = ctk.CTkLabel(main_frame, text="Descrição:", font=("Arial", 12))
        desc_label.pack(anchor="w", pady=(15, 5))
        
        self.description_entry = ctk.CTkEntry(main_frame, height=35)
        self.description_entry.pack(fill="x", pady=(0, 5))
        
        # Substituindo o label por um botão
        self.select_button = ctk.CTkButton(
            main_frame,
            text="",
            image=self.excel_icon,
            fg_color="#FF5722",
            hover_color="#CE461B",
            command=self.open_excel_selector,
            width=32,
            height=32
        )
        self.select_button.pack(anchor="w", pady=(0, 15))
        
        # Adicionar tooltip
        ToolTip(self.select_button, "Procurar descrição no plano de contas")

        activity_label = ctk.CTkLabel(main_frame, text="Atividade:", font=("Arial", 12))
        activity_label.pack(anchor="w", pady=(0, 5))
        
      
        self.activity_entry = ctk.CTkEntry(main_frame, height=35)
        self.activity_entry.configure(validate="key", validatecommand=(self.register(self.validate_activity_input), '%P'))
        self.activity_entry.pack(fill="x", pady=(0, 15))

        self.create_form_field(
            main_frame,
            "Tempo de início:",
            disabled_value=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        end_label = ctk.CTkLabel(main_frame, text="Estimativa de finalização:", font=("Arial", 12))
        end_label.pack(anchor="w", pady=(15, 10))

        selectors_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        selectors_frame.pack(fill="x", pady=(0, 20))

        self.date_picker = DateEntry(
            selectors_frame,
            width=12,
            background='black',
            foreground='orange',
            borderwidth=2,
            date_pattern='dd/mm/yyyy',
            mindate=datetime.now(),
            locale='pt_BR'
        )
        self.date_picker.pack(side="left", padx=(0, 15))

        # Campo de entrada para a hora
        self.time_entry = ctk.CTkEntry(
            selectors_frame,
            height=35,
            placeholder_text="HH:mm"  # Placeholder para indicar o formato
        )
        self.time_entry.pack(side="left", padx=2)

        # Adicionando o evento de entrada para formatar a hora
        self.time_entry.bind("<KeyRelease>", self.format_time_entry)

        # Limitar a entrada a apenas números e no máximo 4 caracteres
        self.time_entry.configure(validate="key", validatecommand=(self.register(self.validate_time_input), '%P'))

        self.confirm_btn = ctk.CTkButton(
            main_frame,
            text="Confirmar",
            fg_color="#FF5722",
            hover_color="#CE461B",
            command=self.create_activity
        )
        self.confirm_btn.pack(pady=5)

        # Configurar navegação por teclado
        self.setup_keyboard_navigation()

    def validate_activity_input(self, new_value):
        if len(new_value) > 250:
            self.bell()  # Faz o som de alerta do sistema
            return False
        return True

    def setup_keyboard_navigation(self):
        """Configura navegação por teclado entre campos"""
        try:
            # Campos na ordem de navegação
            self.description_entry.bind('<Return>', lambda e: self.activity_entry.focus())
            self.activity_entry.bind('<Return>', lambda e: self.time_entry.focus())
            self.time_entry.bind('<Return>', lambda e: self.handle_enter_key(e))
            
            # Bind específico para o botão confirmar
            self.confirm_btn.bind('<Return>', lambda e: self.handle_enter_key(e))
            
        except Exception as e:
            logger.error(f"Erro ao configurar navegação por teclado: {e}")

    def handle_enter_key(self, event=None):
        """Manipula o pressionamento da tecla Enter"""
        try:
            # Verifica qual widget tem o foco
            focused = self.focus_get()
            
            # Se for o campo de tempo, valida e cria a atividade
            if focused == self.time_entry:
                self.create_activity()
            # Se for outro campo, pode adicionar lógica específica aqui
            else:
                self.create_activity()
                
        except Exception as e:
            logger.error(f"Erro ao processar tecla Enter: {e}")

    def create_form_field(self, parent, label_text, disabled_value=None):
        label = ctk.CTkLabel(parent, text=label_text, font=("Arial", 12))
        label.pack(anchor="w", pady=(15, 5))
        
        entry = ctk.CTkEntry(parent, height=35)
        if disabled_value:
            entry.insert(0, disabled_value)
            entry.configure(state="disabled")
        entry.pack(fill="x", pady=(0, 5))
        return entry

    def open_excel_selector(self):
        def on_description_selected(description):
            self.description_entry.delete(0, "end")
            self.description_entry.insert(0, description)
        ExcelSelector(self, on_description_selected)
    
    def create_activity(self):
        """Cria uma nova atividade"""
        try:
            selected_date = self.date_picker.get_date()
            selected_time = self.time_entry.get()
            
            # Validação do formato da hora
            if not self.validate_time(selected_time):
                messagebox.showerror("Erro", "Horário inválido, por favor digite no formato HH:mm.")
                return
                
            hour, minute = map(int, selected_time.split(':'))
            selected_datetime = datetime.combine(selected_date, time(hour=hour, minute=minute))

            description = self.description_entry.get().strip()
            if not description:
                messagebox.showerror("Erro", "A descrição é obrigatória.")
                return

            data = {
                'description': self.description_entry.get(),
                'activity': self.activity_entry.get(),
                'end_time': selected_datetime
            }
            
            success, message = self.logic.create_activity(self.user_data['id'], data)
            
            if success:
                # Chamar o callback com os dados da atividade
                if self.on_activity_created:
                    self.on_activity_created(data)  # Passar os dados da atividade
                self.destroy()
            else:
                logger.warning(f"Falha ao criar atividade: {message}")
                messagebox.showwarning("Aviso", message)
                
        except Exception as e:
            logger.error(f"Erro ao criar atividade: {e}")
            messagebox.showerror("Erro", "Ocorreu um problema ao criar a atividade. Tente novamente mais tarde.")

    def validate_time(self, time_str):
        """Valida se a string de tempo está no formato HH:mm."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, TypeError):
            return False

    def format_time_entry(self, event=None):
        # Obtém o valor da entrada, removendo os dois pontos
        time_str = self.time_entry.get().replace(":", "")

        # Se houver mais de 4 caracteres, corta para 4 caracteres
        if len(time_str) > 4:
            time_str = time_str[:4]

        # Verifica o comprimento da string para decidir sobre o ":".
        if len(time_str) == 4:
            time_str = time_str[:2] + ":" + time_str[2:]  # Insere o ":" quando houver 4 caracteres
        elif len(time_str) < 4:
            # Se houver menos de 4 caracteres, remove o ":"
            if ":" in time_str:
                time_str = time_str.replace(":", "")

        # Atualiza o campo de entrada
        self.time_entry.delete(0, "end")
        self.time_entry.insert(0, time_str)

    def validate_time_input(self, new_value):
        if len(new_value) > 5:  # Limitar a 5 caracteres (HH:mm)
            return False
        if new_value and not all(c.isdigit() or c == ':' for c in new_value):
            return False
        return True
        
    def populate_form_fields(self):
        """Preenche apenas o campo de descrição"""
        try:
            self.description_entry.delete(0, "end")
            self.description_entry.insert(0, self.activity_data.get('description', ''))
        except Exception as e:
            logger.error(f"Erro ao preencher campo de descrição: {e}")