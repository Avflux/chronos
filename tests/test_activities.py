# tests/test_activities.py

import sys
import os
import logging
from datetime import datetime

# Adiciona o diretório raiz do projeto ao PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseConnection
from app.ui.components.activities.logic.activity_table_logic import ActivityTableLogic

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tests/test_activities.log')
    ]
)

logger = logging.getLogger(__name__)

def test_activity_listing(user_id):
    """Testa a listagem de atividades para um usuário específico"""
    try:
        logger.info(f"Testando listagem de atividades para user_id: {user_id}")
        db = DatabaseConnection()
        logic = ActivityTableLogic(db)
        
        # Testa busca de atividades
        activities = logic.get_activities(user_id)
        logger.info(f"Encontradas {len(activities)} atividades")
        
        # Mostra detalhes das atividades encontradas
        for i, activity in enumerate(activities, 1):
            logger.info(f"\nAtividade {i}:")
            for key, value in activity.items():
                logger.info(f"  {key}: {value}")
        
        return bool(activities)
    except Exception as e:
        logger.error(f"Erro no teste de listagem: {e}")
        return False

def test_activity_db_structure():
    """Verifica a estrutura da tabela de atividades"""
    try:
        logger.info("Verificando estrutura da tabela de atividades")
        db = DatabaseConnection()
        
        # Verifica estrutura da tabela
        query = "DESCRIBE atividades"
        columns = db.execute_query(query)
        
        if columns:
            logger.info("\nEstrutura da tabela 'atividades':")
            for column in columns:
                logger.info(f"  {column['Field']}: {column['Type']}")
        
        # Verifica índices
        query = "SHOW INDEX FROM atividades"
        indices = db.execute_query(query)
        
        if indices:
            logger.info("\nÍndices da tabela 'atividades':")
            for index in indices:
                logger.info(f"  {index['Key_name']}: {index['Column_name']}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar estrutura: {e}")
        return False

def test_user_exists(user_id):
    """Verifica se um usuário existe no banco"""
    try:
        logger.info(f"Verificando existência do usuário {user_id}")
        db = DatabaseConnection()
        
        query = "SELECT id, name_id, nome FROM usuarios WHERE id = %s"
        result = db.execute_query(query, (user_id,))
        
        if result:
            user = result[0]
            logger.info(f"Usuário encontrado: {user}")
            return True
        else:
            logger.warning(f"Usuário {user_id} não encontrado")
            return False
    except Exception as e:
        logger.error(f"Erro ao verificar usuário: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando testes de atividades...")
    
    # Solicita o ID do usuário para teste
    user_id = input("Digite o ID do usuário para teste: ")
    try:
        user_id = int(user_id)
        
        if test_user_exists(user_id):
            print(f"✓ Usuário {user_id} existe no banco")
            
            if test_activity_db_structure():
                print("✓ Estrutura da tabela está correta")
            else:
                print("✗ Problemas na estrutura da tabela")
                
            if test_activity_listing(user_id):
                print("✓ Listagem de atividades funcionou")
            else:
                print("✗ Problemas na listagem de atividades")
        else:
            print(f"✗ Usuário {user_id} não encontrado")
    except ValueError:
        print("✗ ID de usuário inválido")