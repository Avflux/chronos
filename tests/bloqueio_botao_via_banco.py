import sys
import os
import time
import threading
from typing import List
import customtkinter as ctk
from abc import ABC, abstractmethod

# Adiciona o diretório raiz ao PATH para importar os módulos da aplicação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseConnection

# Interface para o Subject (Observable)
class LockControlSubject(ABC):
    @abstractmethod
    def attach(self, observer) -> None:
        pass

    @abstractmethod
    def detach(self, observer) -> None:
        pass

    @abstractmethod
    def notify(self) -> None:
        pass

# Interface para o Observer
class LockControlObserver(ABC):
    @abstractmethod
    def update(self, lock_status: bool) -> None:
        pass

# Implementação concreta do Subject
class LockControlMonitor(LockControlSubject):
    def __init__(self, user_id: int):
        self._observers: List[LockControlObserver] = []
        self._user_id = user_id
        self._lock_status = False
        self._running = True
        self._db = DatabaseConnection()
        
        # Inicia thread de monitoramento
        self._monitor_thread = threading.Thread(target=self._check_lock_status)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def attach(self, observer: LockControlObserver) -> None:
        self._observers.append(observer)

    def detach(self, observer: LockControlObserver) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self._lock_status)

    def stop_monitoring(self):
        self._running = False

    def _check_lock_status(self):
        while self._running:
            try:
                query = """
                    SELECT lock_control 
                    FROM atividades 
                    WHERE user_id = %s 
                    AND ativo = TRUE 
                    ORDER BY id DESC 
                    LIMIT 1
                """
                result = self._db.execute_query(query, (self._user_id,))
                
                if result:
                    new_status = bool(result[0]['lock_control'])
                    if new_status != self._lock_status:
                        self._lock_status = new_status
                        self.notify()
                
                time.sleep(1)  # Verifica a cada segundo
            except Exception as e:
                print(f"Erro ao verificar status: {e}")
                time.sleep(5)  # Espera mais tempo em caso de erro

# Implementação concreta do Observer (Botão)
class LockControlButton(ctk.CTkButton, LockControlObserver):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(text="Botão de Teste")

    def update(self, lock_status: bool) -> None:
        self.configure(state="disabled" if lock_status else "normal")
        status_text = "Bloqueado" if lock_status else "Desbloqueado"
        self.configure(text=f"Botão de Teste ({status_text})")

# Janela de teste
class TestWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Teste de Lock Control")
        self.geometry("300x200")
        
        # ID do usuário para teste
        self.user_id = 1  # Ajuste conforme necessário
        
        # Cria o monitor
        self.lock_monitor = LockControlMonitor(self.user_id)
        
        # Cria o botão
        self.test_button = LockControlButton(
            self,
            text="Botão de Teste",
            command=self.button_click
        )
        self.test_button.pack(pady=20)
        
        # Registra o botão como observer
        self.lock_monitor.attach(self.test_button)
        
        # Botão para alternar status no banco
        self.toggle_button = ctk.CTkButton(
            self,
            text="Alternar Status no Banco",
            command=self.toggle_lock_status
        )
        self.toggle_button.pack(pady=20)

    def button_click(self):
        print("Botão clicado!")

    def toggle_lock_status(self):
        try:
            # Obtém status atual
            query = """
                SELECT lock_control 
                FROM atividades 
                WHERE user_id = %s 
                AND ativo = TRUE 
                ORDER BY id DESC 
                LIMIT 1
            """
            db = DatabaseConnection()
            result = db.execute_query(query, (self.user_id,))
            
            if result:
                current_status = bool(result[0]['lock_control'])
                new_status = not current_status
                
                # Atualiza status
                update_query = """
                    UPDATE atividades 
                    SET lock_control = %s 
                    WHERE user_id = %s 
                    AND ativo = TRUE
                """
                db.execute_query(update_query, (new_status, self.user_id))
                print(f"Status alterado para: {new_status}")
            else:
                print("Nenhuma atividade ativa encontrada")
        except Exception as e:
            print(f"Erro ao alternar status: {e}")

    def on_closing(self):
        self.lock_monitor.stop_monitoring()
        self.destroy()

# Função principal para executar o teste
def main():
    app = TestWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
