-- SMS Logs Table
CREATE TABLE IF NOT EXISTS sms_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('LOW_STOCK', 'EXPIRY', 'SUMMARY') NOT NULL,
    product_id INT,
    product_name VARCHAR(255),
    batch_no VARCHAR(50),
    vendor_name VARCHAR(255),
    to_number VARCHAR(20) NOT NULL,
    message_text TEXT NOT NULL,
    status ENUM('SENT', 'FAILED') NOT NULL,
    provider_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    client_id INT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- SMS Settings Table
CREATE TABLE IF NOT EXISTS sms_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT UNIQUE NOT NULL,
    enable_low_stock_sms BOOLEAN DEFAULT FALSE,
    enable_expiry_sms BOOLEAN DEFAULT FALSE,
    default_recipient VARCHAR(20),
    expiry_alert_days INT DEFAULT 30,
    low_stock_threshold INT DEFAULT 10,
    last_low_stock_sms TIMESTAMP NULL,
    last_expiry_sms TIMESTAMP NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
