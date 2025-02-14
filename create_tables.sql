-- Teams Table
CREATE TABLE IF NOT EXISTS equipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users Table
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipe_id INT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    name_id VARCHAR(50),
    senha VARCHAR(255) NOT NULL,
    tipo_usuario ENUM('admin', 'comum') DEFAULT 'comum',
    data_entrada DATE,
    base_value DECIMAL(10,2),
    ociosidade TIME,
    is_logged_in BOOLEAN DEFAULT FALSE,
    status BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (equipe_id) REFERENCES equipes(id)
);

-- Activities Table
CREATE TABLE IF NOT EXISTS atividades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    description TEXT,
    atividade VARCHAR(255) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    time_regress TIME,
    time_exceeded TIME,
    reason VARCHAR(255),
    total_time TIME,
    ativo BOOLEAN DEFAULT TRUE,
    pausado BOOLEAN DEFAULT FALSE,
    concluido BOOLEAN DEFAULT FALSE,
    current_mode VARCHAR(20), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES usuarios(id)
);

-- User Lock/Unlock Table
CREATE TABLE IF NOT EXISTS user_lock_unlock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    lock_status BOOLEAN DEFAULT FALSE,
    unlock_control BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- System Logs Table
CREATE TABLE IF NOT EXISTS logs_sistema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    acao VARCHAR(100) NOT NULL,
    descricao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- System Configuration Table
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default teams
INSERT INTO equipes (nome, descricao) VALUES
('Administrativo', 'Equipe Administrativa'),
('Civil', 'Equipe Civil'),
('Diretoria', 'Equipe Diretoria'),
('Eletromecânico', 'Equipe Eletromecânica'),
('SPCS', 'Equipe SPCS')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);

-- Insert default admin user
INSERT INTO usuarios (nome, email, name_id, senha, tipo_usuario, equipe_id, data_entrada, status) 
SELECT 'Administrator', 'admin@interest.com.br', 'admin', 'admin123', 'admin', e.id, CURRENT_DATE, TRUE
FROM equipes e 
WHERE e.nome = 'administrativo'
LIMIT 1
ON DUPLICATE KEY UPDATE email = email;

-- Insert default lock status for admin user
INSERT INTO user_lock_unlock (user_id, lock_status, unlock_control)
SELECT id, FALSE, TRUE
FROM usuarios
WHERE email = 'admin@interest.com.br'
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Insert default system configurations
INSERT INTO system_config (config_key, config_value) VALUES
('SYSTEM_VERSION', '1.0'),
('MAX_LOGIN_ATTEMPTS', '3')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- Drop trigger if exists
DROP TRIGGER IF EXISTS after_usuario_insert;

-- Create trigger for auto-inserting lock status when a new user is created
DELIMITER //
CREATE TRIGGER after_usuario_insert 
AFTER INSERT ON usuarios
FOR EACH ROW
BEGIN
    INSERT INTO user_lock_unlock (
        user_id, 
        lock_status,
        unlock_control,
        created_at
    ) VALUES (
        NEW.id,
        FALSE,  -- Inicialmente não bloqueado
        TRUE,   -- Controles inicialmente desbloqueados
        NOW()
    );
END //
DELIMITER ;

-- Criar Event Scheduler para resetar is_logged_in
SET GLOBAL event_scheduler = ON;

-- Dropar o evento se já existir
DROP EVENT IF EXISTS reset_user_login_status;

-- Criar evento para resetar is_logged_in todos os dias à meia-noite
CREATE EVENT reset_user_login_status
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY
DO
    UPDATE usuarios 
    SET is_logged_in = FALSE,
        updated_at = CURRENT_TIMESTAMP 
    WHERE is_logged_in = TRUE 
    AND DATE(updated_at) < CURRENT_DATE;

-- Verificar se o Event Scheduler está ativo
SHOW VARIABLES LIKE 'event_scheduler';