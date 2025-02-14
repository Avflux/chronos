import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QWidget, QMessageBox
import win32com.client
import os

class ExcelEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.initUI()
        self.file_path = None

    def initUI(self):
        self.setWindowTitle("Editor de Excel")
        self.setGeometry(100, 100, 400, 200)

        # Layout principal
        layout = QVBoxLayout()

        # Campo para inserir texto
        self.text_label = QLabel("Digite o número para a célula D15:")
        layout.addWidget(self.text_label)

        self.text_input = QLineEdit()
        layout.addWidget(self.text_input)

        # Botão para carregar arquivo xlsx
        self.load_button = QPushButton("Carregar arquivo .xlsx")
        self.load_button.clicked.connect(self.load_file)
        layout.addWidget(self.load_button)

        # Botão para enviar texto
        self.send_button = QPushButton("Enviar número para D15")
        self.send_button.clicked.connect(self.send_text)
        layout.addWidget(self.send_button)

        # Widget principal
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo Excel", "", "Arquivos Excel (*.xlsx);;Todos os Arquivos (*)", options=options)
        if file_path:
            self.file_path = os.path.normpath(file_path)
            QMessageBox.information(self, "Arquivo Carregado", f"Arquivo selecionado: {self.file_path}")

    def send_text(self):
        if not self.file_path:
            QMessageBox.warning(self, "Erro", "Nenhum arquivo carregado!")
            return

        if not os.path.exists(self.file_path):
            QMessageBox.critical(self, "Erro", "O arquivo selecionado não existe ou o caminho é inválido.")
            return

        text = self.text_input.text()
        if not text:
            QMessageBox.warning(self, "Erro", "Por favor, insira um número para enviar.")
            return

        # Substitui vírgulas por pontos para aceitar formato numérico local
        text = text.replace(',', '.')

        try:
            number = float(text)
        except ValueError:
            QMessageBox.critical(self, "Erro", "O valor inserido não é um número válido.")
            return

        try:
            # Inicializa o Excel
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False

            # Abre o arquivo
            workbook = excel.Workbooks.Open(self.file_path)
            sheet = workbook.ActiveSheet

            # Insere o valor na célula D15
            sheet.Range("D15").Value = number

            # Força o recálculo da fórmula
            sheet.Calculate()  # Recalcula apenas a planilha ativa
            workbook.Application.CalculateFull()  # Recalcula todas as fórmulas no workbook

            # Salva e sobrescreve o arquivo original
            workbook.Save()
            QMessageBox.information(self, "Sucesso", "Número enviado para D15 com sucesso e arquivo salvo!")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao processar o arquivo:\n{e}")
        finally:
            # Garante que o Excel seja fechado e liberado
            workbook.Close(SaveChanges=True)
            excel.Quit()
            del workbook
            del excel



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExcelEditor()
    window.show()
    sys.exit(app.exec_())
