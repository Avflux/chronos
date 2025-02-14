# tests/test_database.py

import sys
import os
import logging
from datetime import datetime

# Adiciona o diretório raiz do projeto ao PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseConnection
from app.config.settings import DB_CONFIG

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tests/test_database.log')
    ]
)

logger = logging.getLogger(__name__)

def test_database_connection():
    """Testa a conexão com o banco de dados"""
    try:
        logger.info("Iniciando teste de conexão com o banco de dados")
        db = DatabaseConnection()
        
        # Testa conexão
        connection = db.connect()
        if connection and connection.is_connected():
            logger.info("Conexão estabelecida com sucesso!")
            
            # Mostra configurações (sem senha)
            safe_config = {k:v for k,v in DB_CONFIG.items() if k != 'password'}
            logger.info(f"Configurações: {safe_config}")
            
            return True
        else:
            logger.error("Falha ao conectar ao banco")
            return False
    except Exception as e:
        logger.error(f"Erro no teste de conexão: {e}")
        return False

def test_query_execution():
    """Testa a execução de queries básicas"""
    try:
        logger.info("Iniciando teste de execução de queries")
        db = DatabaseConnection()
        
        # Testa SELECT simples
        query = "SELECT 1"
        result = db.execute_query(query)
        logger.info(f"Resultado do SELECT 1: {result}")
        
        # Lista tabelas do banco
        query = "SHOW TABLES"
        tables = db.execute_query(query)
        logger.info(f"Tabelas encontradas: {tables}")
        
        return True
    except Exception as e:
        logger.error(f"Erro no teste de queries: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando testes de banco de dados...")
    
    if test_database_connection():
        print("✓ Teste de conexão passou")
    else:
        print("✗ Teste de conexão falhou")
        
    if test_query_execution():
        print("✓ Teste de queries passou")
    else:
        print("✗ Teste de queries falhou")