USE Pharmacy_Management;

-- System Configuration Table (Global Settings)
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Default Settings
INSERT INTO system_settings (config_key, config_value, description) VALUES 
('software_name', 'Aarambha PMS', 'Name of the software'),
('software_logo_url', '', 'Primary logo URL'),
('currency_symbol', 'रु', 'Default currency symbol'),
('timezone', 'Asia/Kathmandu', 'Default timezone'),
('smtp_host', '', 'Email server host'),
('smtp_port', '', 'Email server port'),
('smtp_user', '', 'Email server username'),
('smtp_pass', '', 'Email server password'),
('sms_gateway', 'Twilio', 'Primary SMS provider'),
('backup_schedule', 'Daily', 'Database backup frequency (Daily/Weekly)'),
('low_stock_threshold', '15', 'Default global low stock alert limit')
ON DUPLICATE KEY UPDATE config_key=config_key;

-- Announcements / Broadcasts
CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    target_role ENUM('ALL', 'ADMIN', 'CASHIER') DEFAULT 'ALL',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support Ticketing System
CREATE TABLE IF NOT EXISTS support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    user_id INT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('open', 'pending', 'resolved', 'closed') DEFAULT 'open',
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Subscription Invoices (Automated Billing)
CREATE TABLE IF NOT EXISTS subscription_invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    package_id INT NOT NULL,
    invoice_number VARCHAR(50) UNIQUE,
    amount DECIMAL(10, 2),
    billing_date DATE,
    due_date DATE,
    status ENUM('paid', 'unpaid', 'overdue', 'cancelled') DEFAULT 'unpaid',
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

-- Global Master Medicine Database
CREATE TABLE IF NOT EXISTS global_medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    generic_name VARCHAR(255),
    manufacturer VARCHAR(255),
    composition TEXT,
    category VARCHAR(100),
    interaction_warnings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
