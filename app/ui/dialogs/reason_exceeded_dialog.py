import customtkinter as ctk
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)

class ReasonExceededDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, activity_info=None):
        super().__init__(parent)
        
        # Configurações da janela
        self.title("Tempo Excedido")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Remover botões de minimizar e maximizar
        self.overrideredirect(True)  # Remove a barra de título completamente
        
        # Manter janela sempre no topo
        self.attributes('-topmost', True)
        
        # Centralizar na tela do monitor principal
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 600) // 2
        self.geometry(f"500x600+{x}+{y}")

        # Configurar aparência baseada no tema do sistema
        self._set_appearance()
        
        self.activity_info = activity_info
        self.result = None
        self.setup_ui()
        
        # Forçar foco e manter no topo
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Garantir que a janela permaneça no topo mesmo após perder o foco
        self.bind('<FocusOut>', lambda e: self.lift())

    def _set_appearance(self):
        """Configura cores baseadas no tema atual"""
        self.appearance_mode = ctk.get_appearance_mode()  # "Dark" ou "Light"
        
        if self.appearance_mode == "Dark":
            self.configure(fg_color=("gray86", "gray16"))
            self.title_color = "white"
            self.bg_color = "gray16"
            self.frame_color = "gray20"
        else:
            self.configure(fg_color=("gray86", "gray16"))
            self.title_color = "black"
            self.bg_color = "gray86"
            self.frame_color = "gray80"

    def setup_ui(self):
        # Frame principal com borda
        main_frame = ctk.CTkFrame(
            self,
            fg_color=self.frame_color,
            corner_radius=10
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Barra de título personalizada
        title_frame = ctk.CTkFrame(
            main_frame,
            fg_color=self.frame_color,
            height=40
        )
        title_frame.pack(fill="x", pady=(0, 10))
        
        # Título centralizado na barra
        title = ctk.CTkLabel(
            title_frame,
            text="Tempo Excedido!",
            font=("Roboto", 24, "bold"),
            text_color="#FF5722"
        )
        title.pack(pady=10)
        
        # Conteúdo
        content_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True, padx=20)
        
        # Subtítulo com informação da atividade
        if self.activity_info:
            activity_info = f"Atividade: {self.activity_info.get('atividade', 'N/A')}"
        else:
            activity_info = "Atividade não especificada"
            
        subtitle = ctk.CTkLabel(
            content_frame,
            text=activity_info,
            font=("Roboto", 16)
        )
        subtitle.pack(pady=(0, 20))
        
        # Mensagem motivacional com fundo destacado
        motivational_frame = ctk.CTkFrame(
            content_frame,
            fg_color=self.frame_color,
            corner_radius=10
        )
        motivational_frame.pack(fill="x", pady=(0, 20))
        
        motivational_text = (
            "Não se preocupe!\n"
            "Às vezes as coisas levam mais tempo do que o planejado.\n"
            "Vamos entender o motivo para melhorar nossas estimativas?"
        )
        
        motivational_label = ctk.CTkLabel(
            motivational_frame,
            text=motivational_text,
            font=("Roboto", 14),
            wraplength=400,
            justify="center"
        )
        motivational_label.pack(pady=10)
        
        # Frame para o combobox
        combo_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        combo_frame.pack(fill="x", pady=(0, 20))
        
        combo_label = ctk.CTkLabel(
            combo_frame,
            text="Selecione o motivo:",
            font=("Roboto", 14, "bold")
        )
        combo_label.pack(pady=(0, 5))
        
        # Opções do combobox
        self.reasons = [
            "Selecione um motivo...",
            "Tempo Insuficiente",
            "Aguardando definição de Projeto",
            "Falta de conhecimento",
            "Mudança de prioridade",
            "Falta de insumo",
            "Problemas técnicos",
            "Motivos Médicos"
        ]
        
        self.reason_var = ctk.StringVar(value=self.reasons[0])
        self.reason_combo = ctk.CTkComboBox(
            combo_frame,
            values=self.reasons,
            variable=self.reason_var,
            width=300,
            state="readonly",
            command=self.check_button_state
        )
        self.reason_combo.pack()
        
        # Frame para entrada de texto
        text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        text_frame.pack(fill="x", pady=(0, 20))
        
        text_label = ctk.CTkLabel(
            text_frame,
            text="Outros:",
            font=("Roboto", 14, "bold")
        )
        text_label.pack(pady=(0, 5))
        
        self.text_input = ctk.CTkTextbox(
            text_frame,
            width=400,
            height=150
        )
        self.text_input.pack()
        
        # Bind para verificar mudanças no texto
        self.text_input.bind("<<Modified>>", self.on_text_changed)
        
        # Atualizar o botão de enviar com cores adaptativas
        self.submit_button = ctk.CTkButton(
            content_frame,
            text="Enviar",
            font=("Roboto", 14, "bold"),
            fg_color="#FF5722",
            hover_color="#CE461B",
            command=self.submit,
            state="disabled",
            height=40
        )
        self.submit_button.pack(pady=20)

    def on_text_changed(self, event=None):
        self.text_input.edit_modified(False)  # Reset the modified flag
        self.check_button_state()

    def check_button_state(self, event=None):
        reason_selected = self.reason_var.get() != self.reasons[0]
        has_text = len(self.text_input.get("1.0", "end-1c").strip()) > 0
        
        if reason_selected or has_text:
            self.submit_button.configure(state="normal")
        else:
            self.submit_button.configure(state="disabled")

    def submit(self):
        selected_reason = self.reason_var.get()
        other_reason = self.text_input.get("1.0", "end-1c").strip()
        
        if selected_reason == self.reasons[0] and not other_reason:
            messagebox.showwarning(
                "Aviso",
                "Por favor, selecione um motivo ou forneça uma descrição."
            )
            return
        
        self.result = {
            "selected_reason": selected_reason if selected_reason != self.reasons[0] else None,
            "other_reason": other_reason if other_reason else None
        }
        
        self.grab_release()
        self.destroy()

# Interface de teste com tema configurável
if __name__ == "__main__":
    class TestApp(ctk.CTk):
        def __init__(self):
            super().__init__()
            
            self.title("Teste - ReasonExceededDialog")
            self.geometry("300x200")
            
            # Botões para testar diferentes temas
            theme_frame = ctk.CTkFrame(self)
            theme_frame.pack(pady=10)
            
            ctk.CTkButton(
                theme_frame,
                text="Tema Claro",
                command=lambda: ctk.set_appearance_mode("Light")
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                theme_frame,
                text="Tema Escuro",
                command=lambda: ctk.set_appearance_mode("Dark")
            ).pack(side="left", padx=5)
            
            # Botão para abrir o diálogo
            btn = ctk.CTkButton(
                self,
                text="Abrir Diálogo",
                command=self.open_dialog
            )
            btn.pack(expand=True)
            
        def open_dialog(self):
            activity_info = {
                "atividade": "Desenvolvimento de Interface",
                "tempo_estimado": "2:00:00",
                "tempo_real": "3:15:30"
            }
            
            dialog = ReasonExceededDialog(self, activity_info)
            self.wait_window(dialog)
            
            if dialog.result:
                print("Resultado:", dialog.result)
    
    app = TestApp()
    app.mainloop()
