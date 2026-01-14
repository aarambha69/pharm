-- SMS Logs Table for tracking all SMS sent by Super Admin
CREATE TABLE IF NOT EXISTS sms_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sent_by INT DEFAULT 0 COMMENT 'User ID who sent the SMS (0 for system)',
    recipient VARCHAR(20) NOT NULL COMMENT 'Phone number of recipient',
    message TEXT NOT NULL COMMENT 'SMS content',
    status ENUM('sent', 'failed', 'pending') DEFAULT 'pending',
    message_id VARCHAR(100) NULL COMMENT 'SMS provider message ID',
    error_message TEXT NULL COMMENT 'Error message if failed',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sent_by (sent_by),
    INDEX idx_recipient (recipient),
    INDEX idx_status (status),
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
