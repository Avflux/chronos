import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import logging
import os
from ..utils.helpers import BaseDialog
from PIL import Image
import sys
from ..utils.tooltip import ToolTip

logger = logging.getLogger(__name__)

class ExcelSelector(BaseDialog):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.title("Seletor de Descrição")
        
        # Adicionar carregamento do ícone do Excel
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
        
        # Configurar geometria e propriedades da janela
        self.resizable(True, True)
        width = int(self.winfo_screenwidth() * 0.8)
        height = int(self.winfo_screenheight() * 0.8)
        x = int((self.winfo_screenwidth() - width) / 2)
        y = int((self.winfo_screenheight() - height) / 2)
        
        # Agrupar todas as configurações de janela em uma única chamada after
        def configure_window():
            self.geometry(f"{width}x{height}+{x}+{y}")
            self.set_window_icon()
            # Configurações para garantir que a janela fique em cima sem impedir maximização
            self.attributes('-topmost', True)  # Mantém a janela sempre no topo
            self.grab_set()                    # Impede interação com outras janelas
            self.focus_force()                 # Força o foco para esta janela
            self.after(10, lambda: self.attributes('-topmost', False))  # Remove topmost após janela aparecer
        
        self.after(100, configure_window)
        
        # Variáveis
        self.on_select = on_select
        self.excel_path = None
        self.df = None
        self.filtered_df = None
        self.filter_values = {}
        self.filter_widgets = {}
        self.search_vars = {}
        self.all_filter_values = {}
        self.search_entries = {}

        self.setup_ui()
        self.load_last_excel()

    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal com padding reduzido
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame de seleção de arquivo com menos padding
        self.file_frame = ctk.CTkFrame(self.main_frame)
        self.file_frame.pack(fill="x", pady=(0, 10))

        self.file_path = ctk.CTkEntry(
            self.file_frame,
            placeholder_text="Caminho do arquivo Excel...",
            height=30,
            font=("Roboto", 10)
        )
        self.file_path.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Modificar o botão para usar o ícone
        self.browse_btn = ctk.CTkButton(
            self.file_frame,
            text="",  # Remover texto
            image=self.excel_icon,  # Adicionar ícone
            fg_color="#FF5722",
            hover_color="#CE461B",
            command=self.browse_file,
            width=32,  # Definir largura fixa
            height=32  # Definir altura fixa
        )
        self.browse_btn.pack(side="right", padx=5, pady=5)
        
        # Adicionar tooltip
        ToolTip(self.browse_btn, "Localizar planilha do plano de contas")

        # Frame de filtros com título
        filter_container = ctk.CTkFrame(self.main_frame)
        filter_container.pack(fill="x", pady=(0, 0))

        filter_title = ctk.CTkLabel(
            filter_container,
            text="Filtros de Busca",
            font=("Roboto", 15, "bold"),
            text_color="#FF5722"
        )
        filter_title.pack(pady=(1, 2))

        # Canvas para scrolling horizontal dos filtros - removendo o fundo branco
        self.filter_canvas = ctk.CTkCanvas(
            filter_container,
            height=140,
            highlightthickness=0,
            bg=self._apply_appearance_mode(self._fg_color)  # Usa a mesma cor do frame
        )
        filter_scrollbar = ttk.Scrollbar(
            filter_container,
            orient="horizontal",
            command=self.filter_canvas.xview
        )

        self.filter_frame = ctk.CTkFrame(self.filter_canvas, fg_color="transparent")

        # Configurar canvas
        self.filter_canvas.configure(xscrollcommand=filter_scrollbar.set)

        # Pack elementos - centralizando o frame dos filtros
        filter_scrollbar.pack(side="bottom", fill="x")
        self.filter_canvas.pack(side="top", fill="x", expand=True, padx=5, pady=(0, 10))

        # Criar janela no canvas - centralizando
        def center_filter_frame(event=None):
            canvas_width = self.filter_canvas.winfo_width()
            frame_width = self.filter_frame.winfo_reqwidth()
            x = max(0, (canvas_width - frame_width) // 2)
            self.filter_canvas.create_window((x, 0), window=self.filter_frame, anchor="nw")

        # Bind para centralizar quando o tamanho mudar
        self.filter_canvas.bind('<Configure>', center_filter_frame)
        self.filter_frame.bind('<Configure>', self.on_frame_configure)

        # Frame da tabela
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Configuração da tabela
        style = ttk.Style()
        
        # Determina as cores baseado no modo
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#1a1a1a" if is_dark else "#CFCFCF"  # Novo cinza para o tema light
        fg_color = "white" if is_dark else "black"
        
        style.configure(
            "Custom.Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            borderwidth=0,
            rowheight=25
        )

        style.configure(
            "Custom.Treeview.Heading",
            background="#FF5722",
            foreground="black",
            relief="flat",
            borderwidth=1,
            font=('Roboto', 9, 'bold')
        )

        style.map(
            "Custom.Treeview",
            background=[("selected", "#1f538d" if is_dark else "#0078D7")],
            foreground=[("selected", "white")]
        )

        style.map(
            "Custom.Treeview.Heading",
            background=[("active", "#ff7043")],
            foreground=[("active", "black")]
        )

        self.tree = ttk.Treeview(
            self.table_frame,
            show='headings',
            selectmode='browse',
            style="Custom.Treeview"
        )

        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)

        # Frame dos botões
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(0, 5))

        def get_theme_color(light_color, dark_color):
            return light_color if ctk.get_appearance_mode() == "Light" else dark_color

        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            fg_color=get_theme_color("#9E9E9E", "#404040"),
            hover_color=get_theme_color("#8F8F8F", "#333333"),
            command=self.destroy
        )
        self.cancel_btn.pack(side="right", padx=5, pady=5)

        self.select_btn = ctk.CTkButton(
            button_frame,
            text="Selecionar",
            fg_color="#FF5722",
            hover_color="#CE461B",
            command=self.select_description
        )
        self.select_btn.pack(side="right", padx=5, pady=5)

        self.tree.bind("<Double-1>", lambda e: self.select_description())

    def on_frame_configure(self, event):
        """Atualiza a região de scroll do canvas dos filtros"""
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def browse_file(self):
        """Abre diálogo para selecionar arquivo Excel"""
        try:
            file_path = filedialog.askopenfilename(
                title="Selecione o arquivo Excel",
                filetypes=[("Excel files", "*.xlsx *.xls")],
                parent=self  # Janela filha
            )

            if file_path:
                self.excel_path = file_path
                self.file_path.delete(0, "end")
                self.file_path.insert(0, file_path)
                self.save_excel_path(file_path)
                self.load_excel()

        except Exception as e:
            logger.error(f"Erro ao selecionar arquivo: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar arquivo: {e}")

    def load_last_excel(self):
        """Carrega o último arquivo Excel utilizado no selector"""
        try:
            if os.path.exists("config.txt"):
                with open("config.txt", "r") as f:
                    for line in f:
                        if line.startswith("SELECTOR_EXCEL_PATH="):
                            last_path = line.split("=")[1].strip()
                            if os.path.exists(last_path):
                                self.excel_path = last_path
                                self.file_path.delete(0, "end")  # Limpa o campo antes de inserir
                                self.file_path.insert(0, last_path)
                                self.load_excel()
        except Exception as e:
            logger.error(f"Erro ao carregar último Excel: {e}")

    def load_excel(self):
        """Carrega e exibe o conteúdo do arquivo Excel"""
        try:
            if self.excel_path:
                # Lê o arquivo Excel
                df_original = pd.read_excel(self.excel_path)
                
                # Pega os nomes das colunas da primeira linha
                header_row = df_original.iloc[0]
                
                # Substitui os nomes "Unnamed" pelos valores da primeira linha
                new_columns = []
                for i, (col, header_value) in enumerate(zip(df_original.columns, header_row.values)):
                    if 'Unnamed' in str(col):
                        # Usar o valor do header_row.values que já é um array numpy
                        new_columns.append(str(header_row.iloc[i]))  # Alteração feita aqui
                    else:
                        new_columns.append(str(col))
                
                # Atualiza os nomes das colunas
                df_original.columns = new_columns
                
                # Remove as colunas desejadas
                self.df = df_original.iloc[:, 1:-2]  # Mantém todas exceto primeira e últimas duas
                
                # Remove a primeira linha que agora está duplicada como cabeçalho
                self.df = self.df.iloc[1:]
                
                # Reseta o índice após remover a primeira linha
                self.df = self.df.reset_index(drop=True)
                
                self.filtered_df = self.df.copy()
                self.update_filters()
                self.update_table()
                
        except Exception as e:
            logger.error(f"Erro ao carregar Excel: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar Excel: {e}")


    def save_excel_path(self, path):
        """Salva o caminho do Excel do selector no config.txt"""
        try:
            existing_content = []
            if os.path.exists("config.txt"):
                with open("config.txt", "r") as f:
                    existing_content = f.readlines()

            # Remove linha existente com SELECTOR_EXCEL_PATH se houver
            existing_content = [line for line in existing_content 
                                if not line.startswith("SELECTOR_EXCEL_PATH=")]

            # Adiciona novo caminho
            existing_content.append(f"SELECTOR_EXCEL_PATH={path}\n")

            # Salva arquivo mantendo outras linhas
            with open("config.txt", "w") as f:
                f.writelines(existing_content)
        except Exception as e:
            logger.error(f"Erro ao salvar caminho do Excel: {e}")

    def load_excel(self):
        """Carrega e exibe o conteúdo do arquivo Excel"""
        try:
            if self.excel_path:
                # Lê o arquivo Excel
                df_original = pd.read_excel(self.excel_path)
                
                # Pega os nomes das colunas da primeira linha
                header_row = df_original.iloc[0]
                
                # Substitui os nomes "Unnamed" pelos valores da primeira linha
                new_columns = []
                for i, col in enumerate(df_original.columns):
                    if 'Unnamed' in str(col):
                        new_columns.append(str(header_row.iloc[i]))
                    else:
                        new_columns.append(str(col))
                
                # Atualiza os nomes das colunas
                df_original.columns = new_columns
                
                # Remove as colunas indesejadas (0, 7 e 8)
                columns_to_drop = [df_original.columns[i] for i in [0, 7, 8] if i < len(df_original.columns)]
                self.df = df_original.drop(columns=columns_to_drop)
                
                # Remove a primeira linha que agora está duplicada como cabeçalho
                self.df = self.df.iloc[1:]
                
                # Reseta o índice após remover a primeira linha
                self.df = self.df.reset_index(drop=True)
                
                self.filtered_df = self.df.copy()
                self.update_filters()
                self.update_table()
        except Exception as e:
            logger.error(f"Erro ao carregar Excel: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar Excel: {e}")

    def should_show_column(self, col_index, col_name):
        """Verifica se a coluna deve ser mostrada"""
        return col_index not in [0, 7, 8]

    def update_filters(self): # Cria as caixas com o texto de pesquisa e os filtros
        """Atualiza os filtros com base no DataFrame atual"""
        try:
            # Limpa os widgets existentes
            for widget in self.filter_frame.winfo_children():
                widget.destroy()

            # Mantém os valores selecionados anteriormente
            previous_values = {col: var.get() if col in self.filter_values else "Todos" 
                            for col, var in self.filter_values.items()}
            
            self.filter_values.clear()
            self.filter_widgets.clear()
            self.search_vars.clear()
            self.search_entries.clear()

            logger.debug(f"Criando filtros para colunas: {self.df.columns.tolist()}")
            
            for col in self.df.columns:
                logger.debug(f"Criando filtro para coluna: {col}")
                
                # Cria frame para o filtro
                frame = ctk.CTkFrame(
                    self.filter_frame,
                    fg_color="transparent"
                )
                frame.pack(side="left", padx=1, pady=5) # Espaçamentos horizontal (padx) e vertical (pady) das caixas (comboboxes)

                # Frame interno para melhor organização
                inner_frame = ctk.CTkFrame(
                    frame,
                    corner_radius=10,
                    border_width=1
                )
                inner_frame.pack(expand=True, fill="both", padx=5, pady=5)

                # Label do filtro
                label = ctk.CTkLabel(
                    inner_frame,
                    text=col,
                    font=("Helvetica", 12, "bold"),
                    text_color="#FF5722"
                )
                label.pack(pady=(5, 0))

                # Variáveis para o filtro
                self.filter_values[col] = ctk.StringVar(value=previous_values.get(col, "Todos"))
                self.search_vars[col] = ctk.StringVar()

                # Entry para pesquisa
                search_entry = ctk.CTkEntry(
                    inner_frame,
                    textvariable=self.search_vars[col],
                    placeholder_text="Pesquisar...",
                    width=150,
                    height=30
                )
                search_entry.pack(padx=5, pady=5)
                self.search_entries[col] = search_entry

                # Bind da tecla Enter
                search_entry.bind('<Return>', lambda e, c=col: self.handle_search_enter(c))

                # Obter valores disponíveis
                available_values = self.get_available_values(col)
                self.all_filter_values[col] = available_values

                # Combobox para seleção
                combo = ttk.Combobox(
                    inner_frame,
                    textvariable=self.filter_values[col],
                    values=["Todos"] + sorted(available_values),
                    state="readonly",
                    width=20 #Tamanho horizontal das caixas de pesquisa
                )
                combo.pack(padx=5, pady=(0, 8))  #pady é a dist vertical do quadrado onde tem a caixa de pesquisa + filtro

                # Bind para a pesquisa
                self.search_vars[col].trace("w", lambda *args, c=col: self.filter_combobox(c))
                self.filter_values[col].trace("w", lambda *args, c=col: self.apply_filters(trigger_column=c))

                # Armazena referência ao combobox
                self.filter_widgets[col] = combo

        except Exception as e:
            logger.error(f"Erro ao atualizar filtros: {e}")
            messagebox.showerror("Erro", f"Erro ao atualizar filtros: {e}")

    def handle_search_enter(self, column):
        """Manipula o evento de pressionar Enter na pesquisa"""
        combo = self.filter_widgets[column]
        values = combo['values']
        
        # Se houver valores filtrados além do "Todos"
        if len(values) > 1:
            # Seleciona o primeiro valor após "Todos"
            self.filter_values[column].set(values[1])
            
        # Limpa o campo de pesquisa
        self.search_vars[column].set("")
        
        # Move o foco para o próximo campo de pesquisa (se houver)
        current_keys = list(self.search_entries.keys())
        try:
            current_index = current_keys.index(column)
            next_index = (current_index + 1) % len(current_keys)
            next_entry = self.search_entries[current_keys[next_index]]
            next_entry.focus_set()
        except (ValueError, IndexError):
            pass

    def filter_combobox(self, column):
        """Filtra os valores do combobox baseado no texto pesquisado"""
        search_text = self.search_vars[column].get().lower()
        available_values = self.get_available_values(column)
        
        if search_text:
            filtered_values = [val for val in available_values 
                             if str(val).lower().find(search_text) != -1]
        else:
            filtered_values = available_values

        # Atualiza os valores do combobox
        self.filter_widgets[column]['values'] = ["Todos"] + sorted(filtered_values)

    def get_available_values(self, current_column):
        """Obtém valores disponíveis para um filtro considerando os outros filtros ativos"""
        temp_df = self.df.copy()
        
        # Aplica os filtros ativos, exceto o filtro atual
        for col, var in self.filter_values.items():
            if col != current_column and var.get() and var.get() != "Todos":
                temp_df = temp_df[temp_df[col] == var.get()]
        
        # Retorna valores únicos da coluna atual no DataFrame filtrado
        return temp_df[current_column].dropna().unique().tolist()

    def apply_filters(self, trigger_column=None):
        """Aplica os filtros selecionados ao DataFrame"""
        # Começa com o DataFrame original
        temp_df = self.df.copy()
        
        # Aplica os filtros ativos
        active_filters = {}
        for col, var in self.filter_values.items():
            value = var.get()
            if value and value != "Todos":
                temp_df = temp_df[temp_df[col] == value]
                active_filters[col] = value

        # Atualiza o DataFrame filtrado
        self.filtered_df = temp_df

        # Atualiza os valores disponíveis em cada filtro, exceto o que disparou a mudança
        for col, combo in self.filter_widgets.items():
            if col != trigger_column:
                current_value = self.filter_values[col].get()
                available_values = self.get_available_values(col)
                
                # Atualiza os valores do combobox mantendo a pesquisa atual
                search_text = self.search_vars[col].get().lower()
                if search_text:
                    available_values = [val for val in available_values 
                                      if str(val).lower().find(search_text) != -1]
                
                combo['values'] = ["Todos"] + sorted(available_values)
                
                # Se o valor atual não está mais disponível, reseta para "Todos"
                if current_value not in available_values and current_value != "Todos":
                    self.filter_values[col].set("Todos")

        # Atualiza a tabela
        self.update_table()

    def update_table(self):
        """Atualiza a tabela com base no DataFrame filtrado"""
        self.tree.delete(*self.tree.get_children())
        
        if self.filtered_df is not None and not self.filtered_df.empty:
            self.tree['columns'] = list(self.filtered_df.columns)

            for col in self.filtered_df.columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100)

            for _, row in self.filtered_df.iterrows():
                self.tree.insert("", "end", values=list(row))

    def select_description(self):
        """Obtém a descrição selecionada na tabela e retorna ao callback"""
        try:
            selected_item = self.tree.selection()
            if selected_item:
                # Pega todos os valores da linha selecionada
                values = self.tree.item(selected_item[0])['values']
                
                # Como removemos a primeira coluna (índice 0) e as duas últimas,
                # precisamos ajustar o índice para pegar a coluna correta
                # Index 8 corresponde à coluna 9 do Excel original
                description = values[6] if len(values) > 6 else ""
                
                # Chama o callback apenas com a descrição
                self.on_select(description)
                self.destroy()
                
        except Exception as e:
            logger.error(f"Erro ao selecionar descrição: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar descrição: {e}")