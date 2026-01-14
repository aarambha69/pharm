-- Customers table for CRM
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    customer_id VARCHAR(20) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    mobile_number VARCHAR(20),
    address TEXT,
    notes TEXT,
    status ENUM('active', 'blocked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    UNIQUE KEY unique_mobile_client (client_id, mobile_number)
);

-- Add customer_id column to sales table for credit sales tracking
ALTER TABLE sales ADD COLUMN customer_id INT NULL;
ALTER TABLE sales ADD FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL;
