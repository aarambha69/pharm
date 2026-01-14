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
SET FOREIGN_KEY_CHECKS = 0;

-- 1. PACKAGES
CREATE TABLE IF NOT EXISTS packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) DEFAULT 0.00,
    features TEXT,
    max_users INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CLIENTS
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pharmacy_name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    pan_number VARCHAR(50),
    dda_number VARCHAR(50),
    oda_number VARCHAR(50),
    contact_number VARCHAR(20),
    logo_path VARCHAR(255),
    owner_photo_path VARCHAR(255),
    client_id_code VARCHAR(50) UNIQUE,
    package_id INT,
    license_expiry DATE,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

-- 3. USERS
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    password VARCHAR(255) NOT NULL,
    role ENUM('SUPER_ADMIN', 'ADMIN', 'CASHIER') NOT NULL,
    profile_pic VARCHAR(255),
    permissions TEXT,
    status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);


-- 4. DEVICE ACTIVATIONS
CREATE TABLE IF NOT EXISTS device_activations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id VARCHAR(255) NOT NULL UNIQUE,
    user_role ENUM('SUPER_ADMIN','ADMIN','CASHIER') NOT NULL,
    client_id INT,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_by VARCHAR(100),
    is_permanent TINYINT(1) DEFAULT 0,
    status ENUM('active','suspended','revoked') DEFAULT 'active',
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- 5. VENDORS
CREATE TABLE IF NOT EXISTS vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    supplier_code VARCHAR(50),
    Name VARCHAR(100) NOT NULL,
    company_name VARCHAR(150),
    pan_vat VARCHAR(50),
    contact_person VARCHAR(100),
    Phone VARCHAR(20),
    alt_phone VARCHAR(20),
    email VARCHAR(100),
    Address VARCHAR(255),
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    payment_terms VARCHAR(50) DEFAULT 'Cash',
    opening_due DECIMAL(10,2) DEFAULT 0.00,
    current_due DECIMAL(10,2) DEFAULT 0.00,
    bank_info TEXT,
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- 6. MEDICINES
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    item_code VARCHAR(50),
    barcode VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    generic_name VARCHAR(100),
    brand_name VARCHAR(100),
    short_name VARCHAR(50),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    dosage_form VARCHAR(50),
    manufacturer VARCHAR(100),
    strength VARCHAR(50),
    low_stock_threshold INT DEFAULT 10,
    unit VARCHAR(20) DEFAULT 'Pcs',
    avg_cost DECIMAL(15, 2) DEFAULT 0,
    last_purchase_rate DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- 7. CUSTOMERS
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    customer_id VARCHAR(50),
    full_name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(20),
    address TEXT,
    notes TEXT,
    status ENUM('active', 'blocked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- 8. STOCKS
CREATE TABLE IF NOT EXISTS stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    medicine_id INT NOT NULL,
    vendor_id INT,
    batch_number VARCHAR(50) NOT NULL,
    expiry_date DATE,
    quantity INT DEFAULT 0,
    purchase_price DECIMAL(15, 2) DEFAULT 0,
    selling_price DECIMAL(15, 2) DEFAULT 0,
    purchase_item_id INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL
);

-- 9. SALES
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    customer_id INT,
    bill_number VARCHAR(50),
    total_amount DECIMAL(15, 2) DEFAULT 0,
    discount_amount DECIMAL(15, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    grand_total DECIMAL(15, 2) DEFAULT 0,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    payment_method ENUM('Cash', 'Card', 'UPI', 'Credit') DEFAULT 'Cash',
    cashier_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (cashier_id) REFERENCES users(id)
);

-- 10. SALE ITEMS
CREATE TABLE IF NOT EXISTS sale_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_no VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(15, 2),
    total_price DECIMAL(15, 2),
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

-- 11. PURCHASES (GRN)
CREATE TABLE IF NOT EXISTS purchases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grn_no VARCHAR(50) UNIQUE NOT NULL,
    client_id INT NOT NULL,
    supplier_id INT NOT NULL,
    invoice_no VARCHAR(100) NOT NULL,
    purchase_date DATE NOT NULL,
    payment_type ENUM('Cash', 'Credit') DEFAULT 'Cash',
    due_date DATE,
    subtotal DECIMAL(15, 2) DEFAULT 0,
    discount_total DECIMAL(15, 2) DEFAULT 0,
    tax_total DECIMAL(15, 2) DEFAULT 0,
    grand_total DECIMAL(15, 2) DEFAULT 0,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    status ENUM('DRAFT', 'CONFIRMED', 'CANCELLED') DEFAULT 'DRAFT',
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (supplier_id) REFERENCES vendors(id)
);

-- 12. PURCHASE ITEMS
CREATE TABLE IF NOT EXISTS purchase_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_no VARCHAR(50) NOT NULL,
    expiry_date DATE NOT NULL,
    qty INT NOT NULL,
    free_qty INT DEFAULT 0,
    purchase_rate DECIMAL(15, 2) NOT NULL,
    mrp DECIMAL(15, 2) DEFAULT 0,
    discount_amount DECIMAL(15, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    line_total DECIMAL(15, 2) NOT NULL,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

-- 13. PURCHASE RETURNS
CREATE TABLE IF NOT EXISTS purchase_returns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT,
    client_id INT NOT NULL,
    return_no VARCHAR(50) UNIQUE NOT NULL,
    return_date DATE NOT NULL,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    status ENUM('CONFIRMED', 'CANCELLED') DEFAULT 'CONFIRMED',
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (purchase_id) REFERENCES purchases(id)
);

-- 14. PURCHASE RETURN ITEMS
CREATE TABLE IF NOT EXISTS purchase_return_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    return_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_no VARCHAR(50) NOT NULL,
    qty INT NOT NULL,
    rate DECIMAL(15, 2) NOT NULL,
    line_total DECIMAL(15, 2) NOT NULL,
    FOREIGN KEY (return_id) REFERENCES purchase_returns(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

-- 15. SUPPLIER LEDGER
CREATE TABLE IF NOT EXISTS supplier_ledger (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    client_id INT NOT NULL,
    transaction_type ENUM('PURCHASE', 'PAYMENT', 'PURCHASE_RETURN', 'OPENING_BALANCE') NOT NULL,
    transaction_id INT,
    debit DECIMAL(15, 2) DEFAULT 0,
    credit DECIMAL(15, 2) DEFAULT 0,
    balance DECIMAL(15, 2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES vendors(id),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- 16. SYSTEM SETTINGS
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 17. ANNOUNCEMENTS
CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    target_role VARCHAR(50),
    target_client_id INT,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 18. AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    user_id INT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 19. SMS QUEUE (OFFLINE SUPPORT)
CREATE TABLE IF NOT EXISTS sms_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    to_number VARCHAR(20) NOT NULL,
    message_text TEXT NOT NULL,
    status ENUM('pending', 'failed', 'sent', 'resent-queued') DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    last_retry TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 20. SMS LOGS
CREATE TABLE IF NOT EXISTS sms_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT,
    type VARCHAR(50),
    product_id INT,
    product_name VARCHAR(255),
    batch_no VARCHAR(50),
    vendor_name VARCHAR(100),
    to_number VARCHAR(20),
    message_text TEXT,
    status VARCHAR(20),
    provider_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 21. SMS SETTINGS
CREATE TABLE IF NOT EXISTS sms_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL UNIQUE,
    default_recipient VARCHAR(20),
    enable_low_stock_sms BOOLEAN DEFAULT FALSE,
    enable_expiry_sms BOOLEAN DEFAULT FALSE,
    low_stock_threshold INT DEFAULT 10,
    expiry_alert_days INT DEFAULT 90,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- 22. BILL TEMPLATES
CREATE TABLE IF NOT EXISTS bill_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT,
    name VARCHAR(100),
    layout_data JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 23. BILLING CONFIGS
CREATE TABLE IF NOT EXISTS billing_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    vat_enabled BOOLEAN DEFAULT FALSE,
    discount_enabled BOOLEAN DEFAULT TRUE,
    print_size ENUM('A4', 'A5', 'Thermal') DEFAULT 'A5',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

SET FOREIGN_KEY_CHECKS = 1;
`;

db.connect((err) => {
    if (err) {
        console.error('Initial DB Connection Failed:', err);
        process.exit(1);
    }
    console.log('Connected to MySQL. Running full schema setup...');

    db.query(schema, (err, results) => {
        if (err) {
            console.error('Schema Setup Failed:', err.message);
            // process.exit(1); // Don't exit hard, maybe some parts succeeded
        } else {
            console.log('✅ Full Database Schema Applied Successfully.');
        }
        db.end();
        process.exit(0);
    });
});
