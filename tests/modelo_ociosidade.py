import customtkinter as ctk
import time
import threading
from pynput import mouse, keyboard


class IdleDetectorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Detector de Ocosidade")
        self.geometry("400x300")
        
        # Configuração de tempos de ociosidade
        self.mouse_idle_time = ctk.IntVar(value=5)
        self.keyboard_idle_time = ctk.IntVar(value=5)
        
        self.last_mouse_activity = time.time()
        self.last_keyboard_activity = time.time()
        
        # Configurações de interface
        self.create_widgets()
        
        # Inicia os detectores de atividade
        self.start_idle_detection()

    def create_widgets(self):
        # Regulador para mouse
        self.mouse_label = ctk.CTkLabel(self, text="Mouse Idle Time (sec):")
        self.mouse_label.pack(pady=10)
        
        self.mouse_slider = ctk.CTkSlider(
            self, from_=1, to=30, variable=self.mouse_idle_time, command=self.update_mouse_idle_label
        )
        self.mouse_slider.pack()
        
        self.mouse_idle_label = ctk.CTkLabel(self, text=f"{self.mouse_idle_time.get()} sec")
        self.mouse_idle_label.pack(pady=5)
        
        # Regulador para teclado
        self.keyboard_label = ctk.CTkLabel(self, text="Keyboard Idle Time (sec):")
        self.keyboard_label.pack(pady=10)
        
        self.keyboard_slider = ctk.CTkSlider(
            self, from_=1, to=30, variable=self.keyboard_idle_time, command=self.update_keyboard_idle_label
        )
        self.keyboard_slider.pack()
        
        self.keyboard_idle_label = ctk.CTkLabel(self, text=f"{self.keyboard_idle_time.get()} sec")
        self.keyboard_idle_label.pack(pady=5)
        
        # Status de ociosidade
        self.idle_status_label = ctk.CTkLabel(self, text="Status: Active", font=("Arial", 16))
        self.idle_status_label.pack(pady=20)

    def update_mouse_idle_label(self, value):
        self.mouse_idle_label.configure(text=f"{int(float(value))} sec")
        
    def update_keyboard_idle_label(self, value):
        self.keyboard_idle_label.configure(text=f"{int(float(value))} sec")
        
    def start_idle_detection(self):
        # Listeners para mouse e teclado
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_activity)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_activity)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        # Thread para monitorar ociosidade
        self.idle_thread = threading.Thread(target=self.monitor_idle_status, daemon=True)
        self.idle_thread.start()

    def on_mouse_activity(self, *args):
        self.last_mouse_activity = time.time()
        
    def on_keyboard_activity(self, *args):
        self.last_keyboard_activity = time.time()
        
    def monitor_idle_status(self):
        while True:
            mouse_idle = time.time() - self.last_mouse_activity > self.mouse_idle_time.get()
            keyboard_idle = time.time() - self.last_keyboard_activity > self.keyboard_idle_time.get()
            
            if mouse_idle and keyboard_idle:
                self.idle_status_label.configure(text="Status: Idle", text_color="red")
            else:
                self.idle_status_label.configure(text="Status: Active", text_color="green")
            
            time.sleep(1)


if __name__ == "__main__":
    app = IdleDetectorApp()
    app.mainloop()
