import mysql.connector
from mysql.connector import Error
import logging
from ..config.settings import DB_CONFIG, APP_CONFIG
import threading
from queue import Queue
import concurrent.futures

logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            self.initialized = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance
    
    def __enter__(self):
        """Implementa o protocolo de context manager"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Implementa o protocolo de context manager"""
        if exc_type is not None:
            # Se houver uma exceção, faz rollback
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
        else:
            # Se não houver exceção, faz commit
            if self.connection and self.connection.is_connected():
                self.connection.commit()
    
    def execute_query_async(self, query, params=None, callback=None):
        """Executa uma query de forma assíncrona"""
        future = self.thread_pool.submit(self.execute_query, query, params)
        
        if callback:
            future.add_done_callback(
                lambda f: callback(f.result())
            )
        return future

    def fetch_one_async(self, query, params=None, callback=None):
        """Versão assíncrona do fetch_one"""
        future = self.thread_pool.submit(self.fetch_one, query, params)
        
        if callback:
            future.add_done_callback(
                lambda f: callback(f.result())
            )
        return future
    
    def fetch_one(self, query, params=None):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error: {e}")
        return None
    
    def connect(self, timeout=10):
        """Estabelece conexão com o banco de dados com timeout"""
        try:
            if not self.connection or not self.connection.is_connected():
                if APP_CONFIG['debug']:
                    print("Tentando conectar com configurações:", 
                          {k: v for k, v in DB_CONFIG.items() if k != 'password'})
                
                self.connection = mysql.connector.connect(
                    **DB_CONFIG,
                    connection_timeout=timeout
                )
                
                if APP_CONFIG['debug']:
                    print("Conexão estabelecida com sucesso!")
                logger.info("Conexão com o banco de dados estabelecida")
                
            return self.connection
        except Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            if APP_CONFIG['debug']:
                print(f"Erro ao conectar ao banco de dados: {e}")
            return None
    
    def execute_query(self, query, params=None, max_retries=3):
        """Executa uma query no banco de dados"""
        for attempt in range(max_retries):
            try:
                logger.debug(f"[DB_QUERY] Executando query: {query}")  # Temporário para debug
                connection = self.connect()
                if connection:
                    cursor = connection.cursor(dictionary=True)
                    
                    if APP_CONFIG['debug']:
                        print(f"Executando query: {query}")
                        print(f"Parâmetros: {params}")
                    
                    cursor.execute(query, params or ())
                    result = cursor.fetchall()
                    connection.commit()
                    
                    if APP_CONFIG['debug']:
                        print(f"Resultado da query: {result}")
                    
                    return result
            except mysql.connector.errors.OperationalError:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Tentativa {attempt + 1} de {max_retries} falhou. Reconectando...")
                self.connect()
            finally:
                if 'cursor' in locals():
                    cursor.close()