import tkinter as tk
import customtkinter as ctk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)
        self.widget.bind("<ButtonPress>", self.leave)
        self.scheduled = None
        
        # Detectar o modo de aparência atual
        self.appearance_mode = ctk.get_appearance_mode().lower()
        
        # Calcular escala baseada na resolução
        self.scale_factor = self.calculate_scale_factor()

    def calculate_scale_factor(self):
        """Calcula o fator de escala baseado na resolução do monitor"""
        screen_height = self.widget.winfo_screenheight()
        
        # Usar altura da tela como referência
        if screen_height <= 720:
            return 0.8    # Monitores pequenos/baixa resolução
        elif screen_height <= 1080:
            return 1.0    # Full HD (referência base)
        elif screen_height <= 1440:
            return 1.2    # 2K
        else:
            return 1.4    # 4K ou superior
    
    def get_scaled_size(self, base_size):
        """Retorna um tamanho escalado baseado no fator de escala"""
        return int(base_size * self.scale_factor)

    def get_colors(self):
        """Retorna as cores baseadas no tema atual"""
        if self.appearance_mode == "dark":
            return {
                "bg": "#2b2b2b",        # Fundo escuro
                "fg": "#ffffff",         # Texto branco
                "border": "#FF5722"      # Borda laranja (mesma cor dos botões)
            }
        else:
            return {
                "bg": "#f2f2f2",        # Fundo claro
                "fg": "#1a1a1a",         # Texto quase preto
                "border": "#FF5722"      # Borda laranja (mesma cor dos botões)
            }

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        if self.scheduled:
            self.widget.after_cancel(self.scheduled)
            self.scheduled = None
        self.hide_tooltip()

    def motion(self, event=None):
        if self.tooltip:
            # Usar coordenadas relativas à tela atual
            root = self.widget.winfo_toplevel()
            root_x = root.winfo_rootx()
            root_y = root.winfo_rooty()
            
            # Calcular posição relativa ao widget
            widget_x = self.widget.winfo_rootx() - root_x
            widget_y = self.widget.winfo_rooty() - root_y
            
            # Posição do mouse relativa à janela atual
            mouse_x = event.x + widget_x + root_x
            mouse_y = event.y + widget_y + root_y
            
            # Offset do tooltip em relação ao cursor
            x = mouse_x + 15
            y = mouse_y + 10
            
            # Obter dimensões da tela atual
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Ajustar se necessário para manter tooltip dentro da tela
            tooltip_width = self.tooltip.winfo_width()
            tooltip_height = self.tooltip.winfo_height()
            
            if x + tooltip_width > screen_width:
                x = mouse_x - tooltip_width - 5
            if y + tooltip_height > screen_height:
                y = mouse_y - tooltip_height - 5
            
            self.tooltip.wm_geometry(f"+{x}+{y}")

    def schedule(self):
        if self.scheduled:
            self.widget.after_cancel(self.scheduled)
        self.scheduled = self.widget.after(1000, self.show_tooltip)

    def show_tooltip(self):
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        
        colors = self.get_colors()
        
        frame = tk.Frame(
            self.tooltip,
            background=colors["border"],
            bd=0
        )
        frame.pack(expand=True, fill="both", padx=1, pady=1)
        
        # Escalar fonte e padding baseado na resolução
        font_size = self.get_scaled_size(10)  # Base: 10
        padx = self.get_scaled_size(8)        # Base: 8
        pady = self.get_scaled_size(4)        # Base: 4
        
        label = tk.Label(
            frame,
            text=self.text,
            justify='left',
            background=colors["bg"],
            foreground=colors["fg"],
            font=("Roboto", str(font_size), "normal"),
            padx=padx,
            pady=pady
        )
        label.pack()

        self.tooltip.attributes('-alpha', 0.95)
        
        # Adicionar cantos arredondados (simulação com máscara)
        self.tooltip.update_idletasks()
        width = self.tooltip.winfo_width()
        height = self.tooltip.winfo_height()
        
        # Usar posição inicial do mouse
        root = self.widget.winfo_toplevel()
        mouse_x = root.winfo_pointerx()
        mouse_y = root.winfo_pointery()
        
        x = mouse_x + 15
        y = mouse_y + 10
        
        # Ajustar para a tela atual
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        tooltip_width = width
        tooltip_height = height
        
        if x + tooltip_width > screen_width:
            x = mouse_x - tooltip_width - 5
        if y + tooltip_height > screen_height:
            y = mouse_y - tooltip_height - 5
            
        self.tooltip.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None 