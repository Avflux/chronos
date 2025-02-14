from cryptography.fernet import Fernet
import os
import logging
from tkinter import messagebox
import sys
import datetime

# Configurar logger
logger = logging.getLogger(__name__)

class EncryptedSettings:
    def __init__(self):
        self.key_file = "crypto.key"
        self.env_file = ".env.encrypted"

    def _get_fernet(self):
        """Retorna uma instância Fernet com a chave existente"""
        try:
            with open(self.key_file, "rb") as key_file:
                key = key_file.read()
            return Fernet(key)
        except FileNotFoundError:
            error_msg = "Arquivo de chave criptográfica não encontrado.\nExecute o aplicativo de configuração primeiro."
            logger.error(f"Arquivo de chave {self.key_file} não encontrado")
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"Erro ao ler chave de criptografia:\n{str(e)}"
            logger.error(error_msg)
            raise
    
    def decrypt_env(self):
        """Descriptografa e retorna as configurações do ambiente"""
        try:
            if not os.path.exists(self.env_file):
                error_msg = "Arquivo de configurações criptografadas não encontrado.\nExecute o aplicativo de configuração primeiro."
                logger.error(f"Arquivo {self.env_file} não encontrado")
                raise FileNotFoundError(error_msg)
            
            # Lê e descriptografa os dados
            with open(self.env_file, "rb") as env_file:
                encrypted_data = env_file.read()
            
            f = self._get_fernet()
            decrypted_data = f.decrypt(encrypted_data).decode()
            
            # Converte os dados descriptografados em dicionário
            env_dict = {}
            for line in decrypted_data.split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_dict[key.strip()] = value.strip()
            
            logger.debug(f"Chaves encontradas no arquivo: {list(env_dict.keys())}")
            
            return env_dict
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Erro ao descriptografar configurações:\n{str(e)}"
            logger.error(error_msg)
            raise

class ConfigError(Exception):
    """Exceção personalizada para erros de configuração"""
    pass

def load_settings():
    """Carrega as configurações e retorna as configurações ou raise exception"""
    try:
        encrypted_settings = EncryptedSettings()
        env_config = encrypted_settings.decrypt_env()
        
        if hasattr(sys, "_MEIPASS"):
            icons_path = sys._MEIPASS
        else:
            icons_path = os.path.abspath(".")
        
        # Definir caminhos base usando caminhos absolutos
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        resources_path = os.path.join(base_path, 'app', 'resources')

        # Log para debug
        logger.debug(f"Base path: {base_path}")
        logger.debug(f"Resources path: {resources_path}")
        logger.debug(f"Icons path: {icons_path}")

        # Mapeamento entre prefixos MYSQL_ e DB_
        config_mapping = {
            'DB_HOST': ['DB_HOST', 'MYSQL_HOST'],
            'DB_USER': ['DB_USER', 'MYSQL_USER'],
            'DB_PASSWORD': ['DB_PASSWORD', 'MYSQL_PASSWORD'],
            'DB_NAME': ['DB_NAME', 'MYSQL_DATABASE'],
            'DB_PORT': ['DB_PORT', 'MYSQL_PORT'],
        }

        # Converter configurações MYSQL_ para o formato DB_
        normalized_config = {}
        for db_key, possible_keys in config_mapping.items():
            value = None
            for key in possible_keys:
                if key in env_config:
                    value = env_config[key]
                    break
            if value is not None:
                normalized_config[db_key] = value

        # Verifica configurações obrigatórias
        required_configs = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_configs = [config for config in required_configs if config not in normalized_config]
        
        if missing_configs:
            error_msg = (f"Configurações ausentes: {', '.join(missing_configs)}\n"
                        f"Configurações encontradas: {', '.join(env_config.keys())}")
            logger.error(error_msg)
            raise ConfigError(error_msg)

        # Log das configurações carregadas (sem senhas)
        safe_config = {k: v if 'PASSWORD' not in k else '***' for k, v in normalized_config.items()}
        logger.info(f"Configurações normalizadas carregadas: {safe_config}")

        # Definir caminhos dos recursos
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icons_path = os.path.join(base_path, 'icons')

        current_year = datetime.datetime.now().year
        
        return {
            'DB_CONFIG': {
                'host': normalized_config['DB_HOST'],
                'user': normalized_config['DB_USER'],
                'password': normalized_config['DB_PASSWORD'],
                'database': normalized_config['DB_NAME'],
                'port': int(normalized_config.get('DB_PORT', 3306))
            },
            'APP_CONFIG': {
                'title': 'Sistema Chronos',
                'version': '0.0.9',
                'theme': 'system',
                'geometry': '1024x768',
                'copyright_year': current_year,
                'debug': env_config.get('APP_DEBUG', 'False').lower() == 'true',
                'icons': {
                    'app': 'icons/app.ico',
                    'time_exceeded': 'icons/time_exceeded.ico',
                    'break': 'icons/coffee.ico',
                    'water': 'icons/water.ico',
                    'morning': 'icons/morning.ico',
                    'afternoon': 'icons/afternoon.ico',
                    'night': 'icons/night.ico',
                    'success': 'icons/success.ico',
                    'coffee': 'icons/coffee.ico',
                    'productivity': 'icons/productivity.ico',
                    'goal': 'icons/goal.ico',
                    'logo_dark': 'icons/logo_dark.png',
                    'logo_light': 'icons/logo_light.png',
                    'subestacao': 'icons/subestacao.png',
                    'logo_login_dark': 'icons/logo_login_dark.png',
                    'logo_login_light': 'icons/logo_login_light.png'
                },
                'motivational_text': (
                    "2025: Ano da Inovação e Eficiência\n\n"
                    "Transforme cada minuto em progresso.\n"
                    "Gerencie seu tempo com sabedoria e\n"
                    "alcance resultados extraordinários."
                )
            },
            'LOG_CONFIG': {
                'log_dir': 'logs',
                'log_level': env_config.get('LOG_LEVEL', 'DEBUG'),
                'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'log_file': 'chronos.log'
            }
        }
    except (FileNotFoundError, ConfigError) as e:
        error_msg = str(e)
        logger.critical(f"Erro ao carregar configurações: {error_msg}")
        messagebox.showerror("Erro de Configuração", error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Erro inesperado ao carregar configurações: {str(e)}"
        logger.critical(error_msg)
        messagebox.showerror("Erro", error_msg)
        sys.exit(1)

# Carrega as configurações
settings = load_settings()

# Exporta as configurações
DB_CONFIG = settings['DB_CONFIG']
APP_CONFIG = settings['APP_CONFIG']
LOG_CONFIG = settings['LOG_CONFIG']