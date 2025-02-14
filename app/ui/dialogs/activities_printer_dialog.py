import customtkinter as ctk
from tkinter import messagebox
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# Lista de meses em português
MESES = [
    '',  # índice 0 vazio para manter compatibilidade com calendar
    'Janeiro', 'Fevereiro', 'Março', 'Abril',
    'Maio', 'Junho', 'Julho', 'Agosto',
    'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

class MoneyEntry(ctk.CTkEntry):
    """Classe customizada para entrada de valores monetários"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<KeyRelease>', self._format_money)
        self._last_valid_value = "R$ 0,00"
        self.insert(0, self._last_valid_value)
        self._ignore_next_call = False

    def _format_money(self, event):
        if self._ignore_next_call:
            self._ignore_next_call = False
            return

        # Obtém o texto atual e a posição do cursor
        current = self.get().replace("R$ ", "").replace(".", "").replace(",", "").replace(" ", "")
        cursor_position = self.index("insert")
        
        # Remove caracteres não numéricos
        current = re.sub(r'[^\d]', '', current)
        
        # Se estiver vazio, define valor mínimo
        if not current:
            formatted = "R$ 0,00"
        else:
            # Remove zeros à esquerda desnecessários
            current = str(int(current))
            
            # Garante que tenha pelo menos 3 dígitos (incluindo os 2 decimais)
            current = current.zfill(3)
            
            # Separa a parte inteira e decimal
            if len(current) >= 3:
                integer_part = current[:-2]
                decimal_part = current[-2:]
            else:
                integer_part = "0"
                decimal_part = current.zfill(2)
            
            # Formata a parte inteira com pontos
            if len(integer_part) > 3:
                formatted_integer = ""
                for i, digit in enumerate(reversed(integer_part)):
                    if i > 0 and i % 3 == 0:
                        formatted_integer = "." + formatted_integer
                    formatted_integer = digit + formatted_integer
            else:
                formatted_integer = integer_part
            
            formatted = f"R$ {formatted_integer},{decimal_part}"
        
        # Atualiza o valor mantendo o cursor na posição correta
        if self.get() != formatted:
            self._ignore_next_call = True
            self.delete(0, ctk.END)
            self.insert(0, formatted)
            
            # Ajusta a posição do cursor
            new_position = cursor_position
            if cursor_position > len(formatted):
                new_position = len(formatted)
            self.icursor(new_position)

    def get_value(self):
        """Retorna o valor numérico (em centavos)"""
        try:
            value = self.get().replace("R$ ", "").replace(".", "").replace(",", "")
            return int(value)
        except ValueError:
            return 0

class ActivitiesPrinterDialog(ctk.CTkToplevel):
    def __init__(self, parent, generate_report_callback, db_connection, user_id):
        super().__init__(parent)
        
        # Configuração básica da janela
        self.title("Relatório de Atividades")
        self.geometry("500x600")  # Aumentado para acomodar novo frame
        self.resizable(False, False)
        
        # Centralizar a janela
        window_width = 500
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Tornar a janela modal
        self.transient(parent)
        self.grab_set()
        
        # Data atual para valores padrão
        self.current_date = datetime.now()
        
        # Armazenar callback e conexão do banco
        self.generate_report_callback = generate_report_callback
        self.db_connection = db_connection
        self.user_id = user_id
        
        # Buscar valor base atual
        try:
            query = """
                SELECT base_value 
                FROM usuarios 
                WHERE id = %(user_id)s
            """
            result = self.db_connection.execute_query(query, {'user_id': user_id})
            self.base_value = float(result[0]['base_value']) if result and result[0]['base_value'] is not None else 0.0
        except Exception as e:
            logger.error(f"[BASE_VALUE] Erro ao buscar valor base: {str(e)}")
            self.base_value = 0.0
        
        # Configurar interface
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface da caixa de diálogo"""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="Gerador de Relatório de Atividades",
            font=("Roboto", 20, "bold"),
            text_color="#FF5722"
        )
        title_label.pack(pady=(20, 30))
        
        # Frame para conter o texto explicativo e a fórmula lado a lado
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="x", pady=(0, 1))
        
        # Frame da esquerda para o texto explicativo
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 1))
        
        # Texto explicativo
        explanation_text = (
            "Esta ferramenta gera um relatório detalhado em PDF das suas atividades.\n\n"
            "O relatório inclui:\n"
            "• Lista completa das atividades do período selecionado\n"
            "• Tempo gasto em cada atividade\n"
            "• Total de horas trabalhadas\n"
            "• Resumo das atividades\n"
            "• Informações do usuário e equipe\n\n"
            "O relatório será salvo no local de sua escolha em formato PDF."
        )
        
        explanation_label = ctk.CTkLabel(
            left_frame,
            text=explanation_text,
            font=("Roboto", 12),
            justify="left",
            wraplength=200
        )
        explanation_label.pack(pady=10, padx=10)
        
        # Frame da direita para a fórmula
        formula_frame = ctk.CTkFrame(content_frame)
        formula_frame.pack(side="right", fill="both", expand=True, padx=(1, 0))
        
        formula_title = ctk.CTkLabel(
            formula_frame,
            text="Cálculo do Valor",
            font=("Roboto", 14, "bold"),
            text_color="#FF5722"  # Cor laranja para o título
        )
        formula_title.pack(pady=(10, 15))
        
        # Frame para a fórmula em si
        formula_display = ctk.CTkFrame(formula_frame, fg_color="#F3F4F6")
        formula_display.pack(fill="x", padx=10, pady=(0, 10))
        
        # Fórmula geral - com cor personalizada
        formula_general = ctk.CTkLabel(
            formula_display,
            text="(Valor Base × Horas)\n──────────\n(Dias × Hora por Dia)",
            font=("Roboto", 12),
            justify="center",
            text_color="#1E88E5"  # Azul para a fórmula geral
        )
        formula_general.pack(pady=10)
        
        # Valores específicos - com cor personalizada
        self.formula_values = ctk.CTkLabel(
            formula_display,
            text=f"({self.base_value:.2f} × 0.00)\n─────────\n(21 × 8.8)",
            font=("Roboto", 12),
            justify="center",
            text_color="#2E7D32"  # Verde para os valores
        )
        self.formula_values.pack(pady=10)
        
        # Resultado - com cor personalizada
        self.formula_result = ctk.CTkLabel(
            formula_display,
            text="Total = R$ 0.00",
            font=("Roboto", 12, "bold"),
            justify="center",
            text_color="#D32F2F"  # Vermelho para o resultado
        )
        self.formula_result.pack(pady=10)
        
        # Frame para filtros
        filter_frame = ctk.CTkFrame(main_frame)
        filter_frame.pack(fill="x", padx=1, pady=(0, 1))
        
        # Label para filtros
        filter_label = ctk.CTkLabel(
            filter_frame,
            text="Filtros do Relatório",
            font=("Roboto", 14, "bold"),
            text_color="#FF5722"
        )
        filter_label.pack(pady=(10, 15))
        
        # Frame para mês e ano
        date_frame = ctk.CTkFrame(filter_frame)
        date_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Mês
        month_frame = ctk.CTkFrame(date_frame)
        month_frame.pack(side="left", expand=True, padx=5)
        
        ctk.CTkLabel(
            month_frame,
            text="Mês:",
            font=("Roboto", 12)
        ).pack(side="left", padx=5)
        
        months = MESES[1:]  # Remove o índice 0 vazio
        self.month_var = ctk.StringVar(value=MESES[self.current_date.month])
        self.month_combo = ctk.CTkComboBox(
            month_frame,
            values=months,
            variable=self.month_var,
            width=120
        )
        self.month_combo.pack(side="left", padx=5)
        
        # Ano
        year_frame = ctk.CTkFrame(date_frame)
        year_frame.pack(side="left", expand=True, padx=5)
        
        ctk.CTkLabel(
            year_frame,
            text="Ano:",
            font=("Roboto", 12)
        ).pack(side="left", padx=5)
        
        current_year = self.current_date.year
        years = [str(year) for year in range(current_year - 5, current_year + 2)]
        self.year_var = ctk.StringVar(value=str(current_year))
        self.year_combo = ctk.CTkComboBox(
            year_frame,
            values=years,
            variable=self.year_var,
            width=100
        )
        self.year_combo.pack(side="left", padx=5)
        
        # Frame para valor base
        value_frame = ctk.CTkFrame(main_frame)
        value_frame.pack(fill="x", padx=10, pady=(0, 20))
        
        value_label = ctk.CTkLabel(
            value_frame,
            text="Valor Base de Cálculo",
            font=("Roboto", 14, "bold"),
            text_color="#FF5722"
        )
        value_label.pack(pady=(10, 15))
        
        # Frame para entrada e botão
        input_frame = ctk.CTkFrame(value_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Entrada monetária customizada
        self.value_entry = MoneyEntry(
            input_frame,
            placeholder_text="R$ 0,00",
            width=200
        )
        self.value_entry.pack(side="left", padx=(5, 10))
        
        # Define o valor inicial do entry com o valor do banco
        if self.base_value > 0:
            formatted_value = f"R$ {self.base_value:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
            self.value_entry.delete(0, 'end')
            self.value_entry.insert(0, formatted_value)
        
        # Botão OK
        self.ok_button = ctk.CTkButton(
            input_frame,
            text="OK",
            command=self.update_base_value,
            fg_color="#FF5722",
            hover_color="#CE461B",
            width=60
        )
        self.ok_button.pack(side="left")
        
        # Frame para botões principais
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Botão Gerar
        generate_button = ctk.CTkButton(
            button_frame,
            text="Gerar Relatório",
            command=self.handle_generate,
            fg_color="#FF5722",
            hover_color="#CE461B",
            width=150
        )
        generate_button.pack(side="left", padx=10)
        
        # Botão Cancelar
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.destroy,
            fg_color="#FF5722",
            hover_color="#CE461B",
            width=150
        )
        cancel_button.pack(side="right", padx=10)
        
    def update_base_value(self):
        """Atualiza o valor base quando o botão OK é clicado"""
        try:
            # Pega o valor do entry e converte para float
            value_text = self.value_entry.get().replace("R$ ", "").replace(".", "").replace(",", ".")
            value = float(value_text)
            
            # Cria instância de QueryActivities
            from app.core.printer.query.query_activities import QueryActivities
            query = QueryActivities(self.db_connection)
            
            # Atualiza o valor base
            if query.update_user_base_value(self.user_id, value):
                messagebox.showinfo("Sucesso", "Valor base atualizado com sucesso!")
                self.base_value = value
                self.update_formula_display()
            else:
                messagebox.showerror("Erro", "Não foi possível atualizar o valor base.")
                
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor válido.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar valor base: {str(e)}")

    def update_formula_display(self):
        """Atualiza o display da fórmula com os valores atuais"""
        try:
            # Pegar o valor base atual
            value_text = self.value_entry.get().replace("R$ ", "").replace(".", "").replace(",", ".")
            base_value = float(value_text)
            
            # Calcular os valores
            hours = 0.00  # Você pode adicionar um campo para as horas ou pegar do banco
            numerator = base_value * hours
            denominator = 21 * 8.8
            total = numerator / denominator if denominator != 0 else 0
            
            # Atualizar os labels
            self.formula_values.configure(
                text=f"({base_value:.2f} × {hours:.2f})\n─────────\n(21 × 8.8)"
            )
            self.formula_result.configure(
                text=f"Total = R$ {total:.2f}"
            )
        except ValueError:
            pass
        except Exception as e:
            logger.error(f"Erro ao atualizar fórmula: {e}")
            
    def get_selected_date(self):
        """Retorna a data selecionada como um dicionário"""
        month_name = self.month_var.get()
        month_number = MESES.index(month_name)  # Usa a lista em português
        return {
            'month': month_number,
            'year': int(self.year_var.get())
        }
        
    def handle_generate(self):
        """Manipula o clique no botão Gerar"""
        try:
            selected_date = self.get_selected_date()
            self.generate_report_callback(selected_date)
            self.destroy()
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            messagebox.showerror(
                "Erro",
                "Ocorreu um erro ao gerar o relatório. Por favor, tente novamente."
            )
