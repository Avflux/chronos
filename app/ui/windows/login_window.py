# Bibliotecas padrão
import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from PIL import Image
import logging, threading, time, json, os, sys, bcrypt

# Imports locais
from ...database.connection import DatabaseConnection
from app.ui.windows.user_window import UserWindow
from app.ui.windows.admin_window import AdminWindow
from ...utils.helpers import IconMixin
from ...config.settings import APP_CONFIG
from .loading_window import LoadingWindow
from cryptography.fernet import Fernet
from ..notifications.notification_manager import NotificationManager

logger = logging.getLogger(__name__)

# Tentar importar keyring com fallback para armazenamento simples
KEYRING_AVAILABLE = False
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    logger.warning("Keyring não disponível. Usando armazenamento alternativo.")
    
    # Implementação simples de fallback (opcional)
    class SimpleKeyring:
        def __init__(self):
            self.store = {}
            
        def set_password(self, service, username, password):
            if service not in self.store:
                self.store[service] = {}
            self.store[service][username] = password
            
        def get_password(self, service, username):
            return self.store.get(service, {}).get(username)
            
        def delete_password(self, service, username):
            if service in self.store and username in self.store[service]:
                del self.store[service][username]
    
    keyring = SimpleKeyring()

class LoginWindow(ctk.CTk, IconMixin):
    def __init__(self, window_manager=None):
        super().__init__()
        self.window_manager = window_manager
        
        # Remover barra de título e bordas
        self.overrideredirect(True)
        
        # Adicionar cantos arredondados
        if sys.platform.startswith('win'):
            self.wm_attributes('-transparent', 'black')
            self._set_window_style()
        
        # Inicializar atributos
        self.setup_complete = False
        self.setup_error = None
        self.main_frame = None
        
        # Configurar a janela principal
        self.window_width = 900
        self.window_height = 600
        if self.window_manager:
            self.window_manager.position_window(self)
        else:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = int((screen_width - self.window_width) / 2)
            y = int((screen_height - self.window_height) / 2)
            self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        # Inicializar variáveis de movimento
        self.x = None
        self.y = None
        
        # Adicionar funcionalidade de arrastar a janela apenas na barra de título
        self.bind("<Button-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)

        # Esconder janela principal e mostrar loading
        self.withdraw()
        self.loading_window = LoadingWindow(self)
        
        # Iniciar thread de carregamento
        self.setup_thread = threading.Thread(target=self._setup_main_window, daemon=True)
        self.setup_thread.start()
        
        # Iniciar verificação periódica e progresso
        self.check_setup_completion()
        self._update_progress()  
        
        self.service_name = "ChronosSystem"
        
        # Configurar armazenamento de credenciais
        self.credentials_dir = Path.home() / '.chronos'
        self.credentials_file = self.credentials_dir / 'credentials.dat'
        self.key_file = self.credentials_dir / 'key.dat'
        
        # Criar diretório se não existir
        self.credentials_dir.mkdir(exist_ok=True)
        
        # Inicializar sistema de criptografia
        self._init_crypto()

    def start_move(self, event):
        """Inicia o movimento da janela"""
        if event.y <= 40:  # Só permite mover se clicar na barra de título
            self.x = event.x
            self.y = event.y

    def stop_move(self, event):
        """Para o movimento da janela"""
        self.x = None
        self.y = None

    def do_move(self, event):
        """Realiza o movimento da janela"""
        if self.x is not None and self.y is not None:  # Verifica se o movimento foi iniciado
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")

    def _update_progress(self):
        """Atualiza a barra de progresso"""
        try:
            if hasattr(self, 'loading_window') and self.loading_window.winfo_exists():
                current = self.loading_window.progress_bar.get()
                if current < 1:
                    self.loading_window.progress_bar.set(current + 0.01)
                    # Usar lambda para evitar problemas de escopo
                    self.after(100, lambda: self._update_progress())
                    # Adicionar binding para trazer para frente ao receber foco
                    self.bind("<FocusIn>", lambda e: self.lift())
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso: {e}")

    def _setup_main_window(self):
        """Configuração da janela principal em thread separada"""
        try:
            time.sleep(2)  # Carregamento inicial
            
            self.db = DatabaseConnection()
            
            # Executar setup_ui na thread principal
            self.after(0, self.setup_ui)
            
            time.sleep(2)  # Carregamento final
            
            # Sinalizar conclusão
            self.setup_complete = True
            
        except Exception as e:
            logger.error(f"Erro durante setup da janela: {e}")
            self.setup_complete = False
            self.setup_error = str(e)

    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal - usando cores do sistema
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",  # Usar cor transparente para herdar o tema
            corner_radius=0
        )
        self.main_frame.pack(expand=True, fill="both")
        
        # Barra superior com botão de fechar
        title_bar = ctk.CTkFrame(
            self.main_frame,
            fg_color=("gray85", "gray16"),  # Cores para modo claro/escuro
            height=40,
            corner_radius=0
        )
        title_bar.pack(fill="x", pady=0)
        title_bar.pack_propagate(False)
        
        # Título na barra superior
        title_label = ctk.CTkLabel(
            title_bar,
            text="SISTEMA CHRONOS",
            font=("Roboto", 14, 'bold'),
            text_color="#FF5722"  # Manter laranja para destaque
        )
        title_label.pack(side="left", padx=20)
        
        # Botão de fechar
        close_button = ctk.CTkButton(
            title_bar,
            text="✕",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color="#FF5722",
            command=self.destroy,
            corner_radius=0
        )
        close_button.pack(side="right")
        
        # Container principal
        content_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent",
            corner_radius=0
        )
        content_frame.pack(expand=True, fill="both", pady=1)
        
        # Frame da imagem (lado esquerdo)
        image_frame = ctk.CTkFrame(
            content_frame,
            width=500,
            height=560,
            fg_color=("gray80", "gray20"),  # Cores para modo claro/escuro
            corner_radius=15
        )
        image_frame.pack(side="left", fill="both", expand=True, padx=(20, 10))
        image_frame.pack_propagate(False)
        
        try:
            # Carregar e exibir imagem da subestação
            if hasattr(sys, "_MEIPASS"):
                image_path = os.path.join(sys._MEIPASS, 'icons', 'subestacao.png')
            else:
                image_path = os.path.join(os.path.abspath("."), 'icons', 'subestacao.png')
            
            if os.path.exists(image_path):
                pil_image = Image.open(image_path)
                # Redimensionar mantendo proporção
                aspect_ratio = pil_image.width / pil_image.height
                new_width = 550
                new_height = int(new_width / aspect_ratio)
                
                bg_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(new_width, new_height)
                )
                
                image_label = ctk.CTkLabel(
                    image_frame,
                    image=bg_image,
                    text=""
                )
                image_label.pack(pady=20)
                
                # Texto motivacional
                motivational_label = ctk.CTkLabel(
                    image_frame,
                    text=APP_CONFIG['motivational_text'],
                    font=("Roboto", 18),
                    text_color="#FF5722",
                    justify="center"
                )
                motivational_label.pack(pady=20)
                
        except Exception as e:
            logger.error(f"Erro ao carregar imagem: {e}")
        
        # Frame do login (lado direito)
        self.login_frame = ctk.CTkFrame(
            content_frame,
            width=320,
            height=560,
            fg_color=("gray80", "gray20"),  # Cores para modo claro/escuro
            corner_radius=15
        )
        self.login_frame.pack(side="right", fill="both", padx=(10, 20))
        self.login_frame.grid_propagate(False)
        
        # Centralizar os elementos no frame de login
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_columnconfigure(1, weight=1)
        
        # Título
        self.title_label = ctk.CTkLabel(
            self.login_frame, 
            text="Login do Sistema",
            font=("Roboto", 24, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(40, 30))
        
        # Adicionar campos de login e demais elementos
        self.setup_login_fields()

        # Verificar e atualizar atividades ativas
        self._check_and_update_active_activities()

    def setup_login_fields(self):
        """Configura os campos do formulário de login"""
        # Campo de usuário
        self.username_label = ctk.CTkLabel(
            self.login_frame,
            text="ID:",
            font=("Roboto", 14)
        )
        self.username_label.grid(row=1, column=0, columnspan=2, pady=(20, 5), sticky="w", padx=30)
        
        self.username_entry = ctk.CTkEntry(
            self.login_frame,
            width=260,
            height=35,
            placeholder_text="Digite seu ID",
            fg_color=("gray75", "gray25")  # Cores para modo claro/escuro
        )
        self.username_entry.grid(row=2, column=0, columnspan=2, padx=30)
        
        # Campo de senha
        self.password_label = ctk.CTkLabel(
            self.login_frame,
            text="Senha:",
            font=("Roboto", 14)
        )
        self.password_label.grid(row=3, column=0, columnspan=2, pady=(20, 5), sticky="w", padx=30)
        
        self.password_entry = ctk.CTkEntry(
            self.login_frame,
            width=260,
            height=35,
            show="*",
            placeholder_text="Digite sua senha",
            fg_color=("gray75", "gray25")  # Cores para modo claro/escuro
        )
        self.password_entry.grid(row=4, column=0, columnspan=2, padx=30)
        
        # Frame para checkbox e botão
        options_frame = ctk.CTkFrame(
            self.login_frame,
            fg_color="transparent"
        )
        options_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0), padx=30, sticky="ew")
        
        # Checkbox para lembrar credenciais
        self.remember_var = ctk.BooleanVar()
        self.remember_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Lembrar credenciais",
            variable=self.remember_var,
            font=("Roboto", 12),
            checkbox_width=20,
            checkbox_height=20,
            hover_color="#FF5722",
            fg_color="#FF5722"
        )
        self.remember_checkbox.pack(side="left")
        
        # Frame para os botões
        buttons_frame = ctk.CTkFrame(
            self.login_frame,
            fg_color="transparent"
        )
        buttons_frame.grid(row=7, column=0, columnspan=2, pady=(20, 20))
        
        # Botão de login
        self.login_button = ctk.CTkButton(
            buttons_frame,
            text="Entrar",
            fg_color="#FF5722",
            hover_color="#CE461B",
            command=self.validate_login,
            width=120,
            height=40,
            font=("Roboto", 14, "bold")
        )
        self.login_button.pack(side="left", padx=5)
        
        # Botão de cancelar
        self.cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=self.destroy,
            width=120,
            height=40,
            font=("Roboto", 14)
        )
        self.cancel_button.pack(side="left", padx=5)

        # Frame para o logo
        logo_frame = ctk.CTkFrame(
            self.login_frame,
            fg_color="transparent"
        )
        logo_frame.grid(row=8, column=0, columnspan=2, pady=(0, 20))

        version_frame = ctk.CTkFrame(
            self.login_frame,
            fg_color="transparent"
        )
        version_frame.grid(row=10, column=0, columnspan=2, pady=(0, 20))

        version_label = ctk.CTkLabel(
            version_frame,
            text=f"Versão: {APP_CONFIG['version']}",
            font=("Roboto", 12),
            text_color="#FF5722",
            justify="center"
        )
        version_label.pack(pady=20)

        # Logo adaptativo ao tema
        try:
            # Definir caminhos para as duas versões do logo
            if hasattr(sys, "_MEIPASS"):
                logo_dark_path = os.path.join(sys._MEIPASS, 'icons', 'logo_login_dark.png')
                logo_light_path = os.path.join(sys._MEIPASS, 'icons', 'logo_login_light.png')
            else:
                logo_dark_path = os.path.join(os.path.abspath("."), 'icons', 'logo_login_dark.png')
                logo_light_path = os.path.join(os.path.abspath("."), 'icons', 'logo_login_light.png')
            
            if os.path.exists(logo_dark_path) and os.path.exists(logo_light_path):
                # Carregar ambas as versões
                dark_image = Image.open(logo_dark_path)
                light_image = Image.open(logo_light_path)
                
                # Definir um tamanho menor para o logo na tela de login
                logo_width = 150  # Ajuste este valor conforme necessário
                logo_height = int(logo_width * (144.2/262))  # Mantém a proporção original
                
                bg_image = ctk.CTkImage(
                    light_image=light_image,
                    dark_image=dark_image,
                    size=(logo_width, logo_height)
                )
                logo_label = ctk.CTkLabel(logo_frame, image=bg_image, text="")
                logo_label.pack()
            else:
                logger.warning(f"Arquivos de logo não encontrados: {logo_dark_path} ou {logo_light_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar imagens do logo: {e}")
        
        # Bindings
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.validate_login())

        # Carregar credenciais salvas
        self.load_saved_credentials()

    def _check_and_update_active_activities(self):
        """
        Verifica e atualiza o status de atividades que possam estar ativas
        quando o usuário ainda não está logado.
        """
        try:
            # Primeiro, obtém o ID do usuário que está tentando fazer login
            username = self.username_entry.get()
            with DatabaseConnection() as db:
                cursor = db.connection.cursor(dictionary=True)
                try:
                    # Busca o ID do usuário
                    user_query = "SELECT id FROM usuarios WHERE name_id = %s"
                    cursor.execute(user_query, (username,))
                    user_result = cursor.fetchone()
                    
                    if user_result:
                        user_id = user_result['id']
                        # Atualiza apenas as atividades deste usuário
                        activity_query = """
                            UPDATE atividades 
                            SET ativo = 0, pausado = 1 
                            WHERE ativo = 1 AND user_id = %s
                        """
                        cursor.execute(activity_query, (user_id,))
                        db.connection.commit()
                        logger.info(f"Atividades ativas do usuário {username} foram pausadas durante inicialização do login")
                finally:
                    cursor.close()
        except Exception as e:
            logger.error(f"Erro ao verificar/atualizar atividades ativas: {str(e)}")

    def _init_crypto(self):
        """Inicializa o sistema de criptografia"""
        try:
            if self.key_file.exists():
                self.key = self.key_file.read_bytes()
            else:
                self.key = Fernet.generate_key()
                self.key_file.write_bytes(self.key)
            
            self.cipher = Fernet(self.key)
        except Exception as e:
            logger.error(f"Erro ao inicializar criptografia: {e}")
            self.cipher = None

    def save_credentials(self, username, password):
        """Salva as credenciais de forma segura"""
        try:
            if not self.cipher:
                return
                
            data = {
                'username': username,
                'password': password
            }
            
            # Criptografar e salvar
            encrypted = self.cipher.encrypt(json.dumps(data).encode())
            self.credentials_file.write_bytes(encrypted)
            logger.debug("Credenciais salvas com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao salvar credenciais: {e}")

    def load_saved_credentials(self):
        """Carrega as credenciais salvas"""
        try:
            if not self.cipher or not self.credentials_file.exists():
                return
                
            # Ler e descriptografar
            encrypted = self.credentials_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            
            # Preencher campos
            self.username_entry.insert(0, data['username'])
            self.password_entry.insert(0, data['password'])
            self.remember_var.set(True)
            logger.debug("Credenciais carregadas com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais: {e}")

    def verify_password(self, input_password, stored_password):
        """Verifica a senha considerando tanto o formato antigo quanto o novo"""
        try:
            # Tenta verificar como bcrypt
            return bcrypt.checkpw(input_password.encode('utf-8'), stored_password.encode('utf-8'))
        except Exception:
            # Se falhar, verifica no formato antigo (comparação direta)
            return input_password == stored_password

    def validate_login(self):
        """Valida as credenciais do usuário"""
        try:
            username = self.username_entry.get()
            password = self.password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Erro", "Por favor, preencha todos os campos!")
                return
            
            # Primeiro, resetar status de usuários que não fizeram logout no dia anterior
            reset_query = """
                UPDATE usuarios 
                SET is_logged_in = FALSE,
                    updated_at = CURRENT_TIMESTAMP 
                WHERE is_logged_in = TRUE 
                AND DATE(updated_at) < CURRENT_DATE
            """
            self.db.execute_query(reset_query)
            
            # Consulta o usuário no banco
            query = """
                SELECT u.id, u.name_id, u.senha, u.tipo_usuario, u.status, 
                    u.nome, u.email, u.equipe_id, u.data_entrada,
                    e.nome as equipe_nome
                FROM usuarios u
                LEFT JOIN equipes e ON u.equipe_id = e.id
                WHERE u.name_id = %s
            """
            
            result = self.db.execute_query(query, (username,))
            
            if not result:
                messagebox.showerror("Erro", "Usuário não encontrado!")
                return
            
            user = result[0]
            
            # Verifica a senha usando o novo método que suporta bcrypt
            if not self.verify_password(password, user['senha']):
                messagebox.showerror("Erro", "Senha incorreta!")
                return
            
            # Se a senha está no formato antigo, atualiza para bcrypt
            if password == user['senha']:  # Senha ainda no formato antigo
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
                update_password_query = "UPDATE usuarios SET senha = %s WHERE id = %s"
                self.db.execute_query(update_password_query, (hashed_password.decode('utf-8'), user['id']))
                logger.info(f"Senha do usuário {username} atualizada para formato bcrypt")
            
            # Atualiza apenas is_logged_in do usuário
            update_query = """
                UPDATE usuarios 
                SET is_logged_in = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            self.db.execute_query(update_query, (user['id'],))
            
            # Confirma que a atualização foi feita
            verify_query = "SELECT is_logged_in FROM usuarios WHERE id = %s"
            verify_result = self.db.execute_query(verify_query, (user['id'],))
            
            if not verify_result or not verify_result[0]['is_logged_in']:
                logger.error("Falha ao atualizar status de login do usuário")
                messagebox.showerror("Erro", "Falha ao atualizar status de login do usuário")
                return
            
            # Log de login bem-sucedido
            logger.info(f"Usuário {username} logado com sucesso")
            
            # Prepara os dados do usuário para passar para a próxima janela
            user_data = {
                'id': user['id'],
                'name_id': user['name_id'],
                'nome': user['nome'],
                'email': user['email'],
                'equipe_id': user['equipe_id'],
                'equipe_nome': user['equipe_nome'],
                'tipo_usuario': user['tipo_usuario'],
                'data_entrada': user['data_entrada']
            }
            
            # Esconde a janela de login
            self.withdraw()
            
            # Abre a janela apropriada baseada no tipo de usuário
            if user['tipo_usuario'] == 'admin':
                admin_window = AdminWindow(self, user_data)
                if self.window_manager:
                    self.window_manager.position_window(admin_window, parent=self)
                notification_manager = NotificationManager()
                notification_manager.initialize(admin_window, user['nome'])
                notification_manager.show_welcome_message(user['nome'])
            else:
                user_window = UserWindow(self, user_data)
                if self.window_manager:
                    self.window_manager.position_window(user_window, parent=self)
                notification_manager = NotificationManager()
                notification_manager.initialize(user_window, user['nome'])
                notification_manager.show_welcome_message(user['nome'])
            
            # Salva as credenciais se a opção estiver marcada
            if self.remember_var.get():
                self.save_credentials(username, password)
            
        except Exception as e:
            logger.error(f"Erro durante login: {e}")
            messagebox.showerror("Erro", "Erro ao realizar login. Por favor, tente novamente.")

    def check_setup_completion(self):
        """Verifica se a configuração foi concluída"""
        try:
            if self.setup_complete:
                self.after(1000, self.show_main_window)
            elif self.setup_error:
                messagebox.showerror("Erro", f"Erro ao inicializar: {self.setup_error}")
                self.destroy()
            else:
                self.after(100, self.check_setup_completion)
        except Exception as e:
            logger.error(f"Erro ao verificar conclusão: {e}")

    def show_main_window(self):
        """Mostra a janela principal e destrói o loading"""
        try:
            if hasattr(self, 'loading_window') and self.loading_window.winfo_exists():
                self.loading_window.destroy()
            self.deiconify()
            self.after(100, self.set_window_icon)
            
            # Forçar janela para frente
            self.lift()
            self.attributes('-topmost', True)
            self.after(100, lambda: self.attributes('-topmost', False))
            self.focus_force()
            
            # Focar no campo de usuário
            if hasattr(self, 'username_entry'):
                self.username_entry.focus()
        except Exception as e:
            logger.error(f"Erro ao mostrar janela principal: {e}")

    def on_closing(self, window):
        """Manipula o fechamento da janela"""
        window.destroy()
        self.master.deiconify()  # Mostra a janela principal novamente

    def _set_window_style(self):
        """Configura o estilo da janela com cantos arredondados no Windows"""
        try:
            from ctypes import windll, byref, sizeof, c_int
            
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_PREFERENCE = c_int
            DWMWCP_ROUND = 2
            
            windll.dwmapi.DwmSetWindowAttribute(
                windll.user32.GetParent(self.winfo_id()),
                DWMWA_WINDOW_CORNER_PREFERENCE,
                byref(DWM_WINDOW_CORNER_PREFERENCE(DWMWCP_ROUND)),
                sizeof(c_int)
            )
        except Exception as e:
            logger.error(f"Erro ao configurar cantos arredondados: {e}")

    def destroy(self):
        if hasattr(self, 'system_tray'):
            self.system_tray.cleanup()
        super().destroy()