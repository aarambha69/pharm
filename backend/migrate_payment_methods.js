const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME,
    multipleStatements: true
});

const schema = `
-- Payment Methods Table
CREATE TABLE IF NOT EXISTS payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    category ENUM('CASH', 'DIGITAL') NOT NULL,
    provider VARCHAR(100),
    account_name VARCHAR(100),
    account_id VARCHAR(100),
    phone_number VARCHAR(20),
    notes TEXT,
    qr_image_path VARCHAR(255),
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    show_on_billing BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    UNIQUE KEY unique_name_per_client (client_id, name)
);

-- Update sales table to include payment method details
ALTER TABLE sales 
ADD COLUMN payment_category ENUM('CASH', 'DIGITAL') DEFAULT 'CASH' AFTER payment_method,
ADD COLUMN payment_method_id INT AFTER payment_category,
ADD COLUMN transaction_ref VARCHAR(100) AFTER payment_method_id,
ADD FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id) ON DELETE SET NULL;

-- Create QR images directory structure (handled by backend)
-- Images will be stored at: backend/uploads/payment_qr/<client_id>/<method_id>.png
`;

db.connect((err) => {
    if (err) {
        console.error('Database connection failed:', err);
        process.exit(1);
    }

    db.query(schema, (err) => {
        if (err) {
            console.error('Migration failed:', err.message);
        } else {
            console.log('✅ Payment methods schema created successfully');
            console.log('✅ Sales table updated with payment tracking fields');
        }
        db.end();
    });
});
