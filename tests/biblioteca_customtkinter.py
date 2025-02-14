import customtkinter as ctk

# Configurar a aparência geral
ctk.set_appearance_mode("System")  # Modo de aparência (System, Light, Dark)
ctk.set_default_color_theme("blue")  # Tema de cores padrão

# Criar a Janela Principal
app = ctk.CTk()
app.geometry("800x600")
app.title("Interface de Ferramentas - customtkinter")

# Criar um frame para organizar os widgets
scrollable_frame = ctk.CTkScrollableFrame(app, width=750, height=550)
scrollable_frame.pack(pady=20, padx=20, fill="both", expand=True)

# Adicionar Exemplos de Widgets
#widgets = [
    #ctk.CTkLabel(scrollable_frame, text="Exemplo de Label"),
    #ctk.CTkButton(scrollable_frame, text="Botão"),
    #ctk.CTkEntry(scrollable_frame, placeholder_text="Digite aqui"),
    #ctk.CTkSlider(scrollable_frame, from_=0, to=100),
    #ctk.CTkCheckBox(scrollable_frame, text="Marque-me"),
    #ctk.CTkRadioButton(scrollable_frame, text="Opção 1", value=1),
    #ctk.CTkRadioButton(scrollable_frame, text="Opção 2", value=2),
    #ctk.CTkProgressBar(scrollable_frame),
    #ctk.CTkSwitch(scrollable_frame, text="Interruptor"),
    #ctk.CTkComboBox(scrollable_frame, values=["Opção A", "Opção B", "Opção C"]),
    #ctk.CTkTextbox(scrollable_frame, width=400, height=100, text="Texto aqui..."),
    #ctk.CTkSegmentedButton(scrollable_frame, values=["Seg1", "Seg2", "Seg3"]),
    #ctk.CTkOptionMenu(scrollable_frame, values=["Item 1", "Item 2"]),
    #ctk.CTkCanvas(scrollable_frame, width=400, height=200, bg="white"),
#]

# Adicionar Widgets no Frame
#for widget in widgets:
    #widget.pack(pady=10)

# Adicionar widgets
# 1. Botões
button = ctk.CTkButton(scrollable_frame, text="Clique Aqui", command=lambda: print("Botão pressionado"))
button.pack(pady=10)

# 2. Label
label = ctk.CTkLabel(scrollable_frame, text="Este é um Label!", text_color="blue")
label.pack(pady=10)

# 3. Entrada de Texto
entry = ctk.CTkEntry(scrollable_frame, placeholder_text="Digite algo aqui...")
entry.pack(pady=10)

# 4. Slider
slider = ctk.CTkSlider(scrollable_frame, from_=0, to=100)
slider.pack(pady=10)

# 5. Checkbox
checkbox = ctk.CTkCheckBox(scrollable_frame, text="Checkbox")
checkbox.pack(pady=10)

# 6. Radiobuttons
radio_var = ctk.StringVar(value="op1")
radio1 = ctk.CTkRadioButton(scrollable_frame, text="Opção 1", variable=radio_var, value="op1")
radio2 = ctk.CTkRadioButton(scrollable_frame, text="Opção 2", variable=radio_var, value="op2")
radio1.pack(pady=5)
radio2.pack(pady=5)

# 7. Progress Bar
progressbar = ctk.CTkProgressBar(scrollable_frame, orientation="horizontal", width=200)
progressbar.set(0.5)  # Configurar o progresso inicial
progressbar.pack(pady=10)

# 8. Switch
switch = ctk.CTkSwitch(scrollable_frame, text="Ativar/Desativar")
switch.pack(pady=10)

# 9. Combobox (Menu Dropdown)
combobox = ctk.CTkComboBox(scrollable_frame, values=["Opção A", "Opção B", "Opção C"])
combobox.set("Opção A")  # Valor inicial
combobox.pack(pady=10)

# 10. Textbox
textbox = ctk.CTkTextbox(scrollable_frame, width=400, height=100)
textbox.insert("0.0", "Escreva seu texto aqui...")
textbox.pack(pady=10)

# 11. Botão de Tamanho Dinâmico
dynamic_button = ctk.CTkButton(scrollable_frame, text="Dinâmico", width=100, height=50)
dynamic_button.pack(pady=10)

# 12. CTkScrollableFrame (Frame com barra de rolagem)
scrol_frame = ctk.CTkScrollableFrame(scrollable_frame, width=300, height=100)
scrol_frame.pack(pady=10)

for i in range(20):
    label = ctk.CTkLabel(scrol_frame, text=f"Item {i+1}")
    label.pack(pady=2)

#13 CTkTabview (Gerenciamento de Abas)
tabview = ctk.CTkTabview(scrollable_frame, width=400, height=50)
tabview.pack(pady=10)

tabview.add("Aba 1")
tabview.add("Aba 2")

label_tab1 = ctk.CTkLabel(tabview.tab("Aba 1"), text="Conteúdo da Aba 1")
label_tab1.pack(pady=10)

label_tab2 = ctk.CTkLabel(tabview.tab("Aba 2"), text="Conteúdo da Aba 2")
label_tab2.pack(pady=10)

#14 CTkSegmentedButton (Botões Segmentados)
segmented_button = ctk.CTkSegmentedButton(scrollable_frame, values=["Opção 1", "Opção 2", "Opção 3"])
segmented_button.set("Opção 1")  # Configura valor inicial
segmented_button.pack(pady=10)

#15 Alterando Modo de Aparência
dark_mode_switch = ctk.CTkSwitch(scrollable_frame, text="Modo Escuro", command=lambda: ctk.set_appearance_mode("Dark"))
light_mode_switch = ctk.CTkSwitch(scrollable_frame, text="Modo Claro", command=lambda: ctk.set_appearance_mode("Light"))

dark_mode_switch.pack(pady=5)
light_mode_switch.pack(pady=5)

# 16 CTkOptionMenu (Menu Dropdown)
option_menu = ctk.CTkOptionMenu(scrollable_frame, values=["Escolha A", "Escolha B", "Escolha C"])
option_menu.set("Escolha A")  # Valor inicial
option_menu.pack(pady=10)

# 17 Fontes: CTkFont permite personalizar tamanho e estilo de fonte.
font = ctk.CTkFont(family="Arial", size=16, weight="bold")
custom_label = ctk.CTkLabel(scrollable_frame, text="Texto com Fonte Personalizada", font=font)
custom_label.pack(pady=10)

# 18 Criar o CTkCanvas
canvas = ctk.CTkCanvas(scrollable_frame, width=400, height=300, bg="white", highlightthickness=0)
canvas.pack(pady=20)

# Desenhar no Canvas
# 1. Retângulo
canvas.create_rectangle(50, 50, 200, 150, fill="blue", outline="black", width=2)

# 2. Círculo (Oval)
canvas.create_oval(100, 100, 250, 200, fill="green", outline="black", width=2)

# 3. Linha
canvas.create_line(10, 10, 300, 250, fill="red", width=3)

# 4. Texto
canvas.create_text(200, 20, text="Exemplo de CTkCanvas", font=("Arial", 16), fill="purple")


# Loop principal
app.mainloop()