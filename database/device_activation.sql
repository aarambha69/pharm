-- Add activation tracking table
CREATE TABLE IF NOT EXISTS device_activations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id VARCHAR(255) UNIQUE NOT NULL,
    user_role ENUM('SUPER_ADMIN', 'ADMIN', 'CASHIER') NOT NULL,
    client_id INT NULL,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_by VARCHAR(100),
    is_permanent BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Activate Super Admin device permanently
INSERT INTO device_activations (machine_id, user_role, activated_by, is_permanent) 
VALUES ('SUPER_ADMIN_DEVICE', 'SUPER_ADMIN', 'System', TRUE)
ON DUPLICATE KEY UPDATE is_permanent = TRUE;
