import mysql.connector
from mysql.connector import Error

def test_connection():
    try:
        # Tentativa de conexão
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Gaadvd@1',
            database='chronos_db'
        )
        
        if connection.is_connected():
            print("Conectado ao banco de dados com sucesso!")
            
            # Teste de select
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE nome = 'admin'")
            result = cursor.fetchall()
            print("\nResultado da consulta:")
            print(result)
            
            # Informações do servidor
            db_info = connection.get_server_info()
            print("\nInformações do servidor MySQL:", db_info)
            
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()
            print("Banco de dados conectado:", db_name)
            
    except Error as e:
        print("Erro ao conectar ao MySQL:", e)
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexão encerrada")

if __name__ == "__main__":
    test_connection()