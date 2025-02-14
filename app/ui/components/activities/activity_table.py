import customtkinter as ctk
from tkinter import ttk
import threading
import time
import logging
from ..logic.activity_table_logic import ActivityTableLogic

logger = logging.getLogger(__name__)

class ActivityTable(ctk.CTkFrame):
    def __init__(self, parent, user_data, db):
        super().__init__(parent)
        self.logic = ActivityTableLogic(db)
        self.user_data = user_data
        self.update_thread = None
        self.should_update = True
        self.current_period = "Dia"
        self.last_update = 0  # Força primeira atualização imediata
        self.setup_ui()
        self.configure_ttk_style()
        self.start_update_thread()
        
        # Bind para quando a janela for fechada
        self.bind('<Destroy>', self.on_destroy)
        
    def configure_ttk_style(self):
        """Configura o estilo do ttk"""
        self.style = ttk.Style()
        
        # Determina as cores baseado no modo
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2b2b2b" if is_dark else "#C9C9C9"  # Novo cinza para o tema light
        fg_color = "white" if is_dark else "black"
        
        # Configuração base do Treeview
        self.style.configure(
            "Custom.Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            borderwidth=0
        )
        
        # Configuração do Treeview quando selecionado
        self.style.map(
            "Custom.Treeview",
            background=[("selected", "#1f538d" if is_dark else "#0078D7")],
            foreground=[("selected", "white")]
        )
        
        # Configuração do cabeçalho
        self.style.configure(
            "Treeview.Heading",
            background="#ff5722",
            foreground="black",
            relief="flat",
            font=('Helvetica', 10, 'bold')
        )
        
        # Configuração do cabeçalho quando hover
        self.style.map(
            "Treeview.Heading",
            background=[("active", "#ff7043")],
            foreground=[("active", "black")]
        )
        
        # Configuração da scrollbar
        self.style.configure(
            "Custom.Vertical.TScrollbar",
            background="#333333" if is_dark else "#E0E0E0",
            bordercolor="#333333" if is_dark else "#E0E0E0",
            arrowcolor="white" if is_dark else "black",
            troughcolor="#2b2b2b" if is_dark else "#F5F5F5"
        )
        
    def setup_ui(self):
        """Configura a interface da tabela"""
        # Frame para conter a tabela e scrollbar
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill="both", expand=True)
        
        # Configurar colunas com larguras específicas
        columns = {
            "id": {"width": 0, "stretch": False, "text": "ID"},
            "description": {"width": 200, "stretch": True, "text": "Descrição"},
            "atividade": {"width": 100, "stretch": True, "text": "Atividade"},
            "start_time": {"width": 120, "stretch": False, "text": "Início"},
            "end_time": {"width": 150, "stretch": False, "text": "Finalização Prevista"},
            "time_exceeded": {"width": 120, "stretch": False, "text": "Tempo Excedido"},
            "total_time": {"width": 100, "stretch": False, "text": "Tempo Total"},
            "status": {"width": 80, "stretch": False, "text": "Status"}
        }
        
        # Criar Treeview
        self.tree = ttk.Treeview(
            self.table_frame,
            columns=list(columns.keys()),
            show='headings',
            style="Custom.Treeview"
        )
        
        # Configurar colunas
        for col, config in columns.items():
            self.tree.heading(col, text=config["text"])
            self.tree.column(
                col,
                width=config["width"],
                stretch=config["stretch"],
                anchor="center"
            )
        
        # Bind duplo clique
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Criar scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.table_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Custom.Vertical.TScrollbar"
        )
        
        # Configurar scrollbar
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configurar pesos do grid
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)

    def on_double_click(self, event):
        """Manipula o duplo clique em uma atividade"""
        try:
            item = self.tree.selection()[0]
            values = self.tree.item(item)['values']
            
            activity_data = {
                'description': values[1]  # Apenas a descrição
            }
            
            # Acessa o ActivityControls através da janela principal
            main_window = self.winfo_toplevel()
            if hasattr(main_window, 'activity_controls'):
                main_window.activity_controls.open_on_double_click_activity_form(activity_data)
                    
        except IndexError:
            pass
        except Exception as e:
            logger.error(f"Erro ao processar duplo clique: {e}")

    def start_update_thread(self):
        self.should_update = True
        self.update_thread = threading.Thread(
            target=self.update_loop,
            daemon=True
        )
        self.update_thread.start()
        
    def update_loop(self):
        """Loop de atualização otimizado para atualizar a cada minuto"""
        while self.should_update:
            try:
                current_time = time.time()
                # Verifica se passou 5 segundos desde a última atualização
                if current_time - self.last_update >= 5:
                    logger.debug("[TABLE] Executando atualização periódica")
                    # Usa o after_idle para garantir execução na thread principal
                    if self.winfo_exists():
                        self.after_idle(self.update_activities)
                    self.last_update = current_time
                
                # Dormir por 1 segundo antes da próxima verificação
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Erro no loop de atualização: {e}")
                time.sleep(5)  # Espera mais tempo em caso de erro

    def start_update_thread(self):
        """Inicia a thread de atualização apenas se o widget existir"""
        if self.winfo_exists():
            self.should_update = True
            self.update_thread = threading.Thread(
                target=self.update_loop,
                daemon=True
            )
            self.update_thread.start()

    def update_activities(self, filter_period=None):
        """Atualiza a lista de atividades com melhor logging"""
        try:
            if not self.winfo_exists():
                return
            
            # Atualiza o período apenas se um novo for explicitamente passado
            if filter_period is not None:
                self.current_period = filter_period
                logger.debug(f"[TABLE] Período atualizado para: {self.current_period}")
            
            logger.debug(f"[TABLE] Iniciando atualização periódica - {time.strftime('%H:%M:%S')}")
            activities = self.logic.get_activities(self.user_data['id'], self.current_period)
            
            # Salvar seleção atual
            selected_items = self.tree.selection()
            selected_ids = [self.tree.item(item)['values'][0] for item in selected_items]
            
            # Determina as cores baseado no modo
            is_dark = ctk.get_appearance_mode() == "Dark"
            
            # Define cores para cada status baseado no tema
            status_colors = {
                'Ativo': '#FF0000' if is_dark else '#FF0000',    # Vermelho mais suave no dark
                'Pausado': '#00AA46' if is_dark else '#377D22',  # Verde mais escuro no light
                'Concluído': '#848484'  # Cinza igual para ambos
            }
            
            # Limpar tabela
            self.tree.delete(*self.tree.get_children())
            
            # Preencher dados
            for activity in activities:
                values = (
                    activity['id'],
                    activity['description'],
                    activity['atividade'],
                    activity['start_time'],
                    activity['end_time'],
                    activity['time_exceeded'],
                    activity['total_time'],
                    activity['status']
                )
                item = self.tree.insert('', 'end', values=values)
                
                # Aplicar cores baseado no status e tema
                status = activity['status']
                if status in status_colors:
                    color = status_colors[status]
                    tag_name = f'{status.lower()}'
                    self.tree.tag_configure(tag_name, foreground=color)
                    self.tree.item(item, tags=(tag_name,))
                
                # Restaurar seleção
                if activity['id'] in selected_ids:
                    self.tree.selection_add(item)
            
            logger.debug(f"[TABLE] Atualização concluída - {time.strftime('%H:%M:%S')}")
                    
        except Exception as e:
            logger.error(f"[TABLE] Erro ao atualizar atividades: {e}")
                
    def on_destroy(self, event):
        self.should_update = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)