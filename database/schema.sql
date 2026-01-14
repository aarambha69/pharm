CREATE DATABASE IF NOT EXISTS Pharmacy_Management;
USE Pharmacy_Management;

-- Packages Table
CREATE TABLE IF NOT EXISTS packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    features TEXT,
    price DECIMAL(10, 2),
    duration_days INT DEFAULT 365,
    max_users VARCHAR(20) DEFAULT 'Unlimited',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clients Table (Pharmacies)
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pharmacy_name VARCHAR(100) NOT NULL,
    address TEXT,
    pan_number VARCHAR(20),
    dda_number VARCHAR(50),
    oda_number VARCHAR(20),
    contact_number VARCHAR(20),
    client_id_code VARCHAR(20) UNIQUE,
    package_id INT,
    machine_id VARCHAR(255),
    license_key VARCHAR(255),
    license_expiry DATE,
    status ENUM('active', 'inactive', 'locked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    name VARCHAR(100),
    role ENUM('SUPER_ADMIN', 'ADMIN', 'CASHIER') NOT NULL,
    client_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Medicines Table
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    manufacturer VARCHAR(100),
    min_quantity INT DEFAULT 10,
    unit VARCHAR(20) DEFAULT 'Pcs',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Stock Table
CREATE TABLE IF NOT EXISTS stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_number VARCHAR(50),
    expiry_date DATE,
    quantity INT DEFAULT 0,
    purchase_price DECIMAL(10, 2),
    selling_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

-- Sales Table
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    cashier_id INT NOT NULL,
    customer_name VARCHAR(100),
    customer_contact VARCHAR(20),
    bill_number VARCHAR(50) UNIQUE,
    total_amount DECIMAL(10, 2),
    vat_amount DECIMAL(10, 2),
    discount_amount DECIMAL(10, 2),
    grand_total DECIMAL(10, 2),
    payment_mode ENUM('Cash', 'PhonePay', 'Card', 'Credit') DEFAULT 'Cash',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (cashier_id) REFERENCES users(id)
);

-- Sale Items Table
CREATE TABLE IF NOT EXISTS sale_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_number VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

-- Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(20),
    address TEXT,
    pan_number VARCHAR(20),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Initial Data
INSERT INTO users (phone, password, email, name, role) 
VALUES ('9855062769', '987654321', 'aarambhaaryal.dev@gmail.com', 'Aarambha Aryal', 'SUPER_ADMIN');

INSERT INTO packages (name, features, price, duration_days, max_users) VALUES 
('Basic Package', 'Basic billing, 1 user, 100 medicines', 5000, 365, '1'),
('Standard Package', 'Advanced billing, 5 users, 500 medicines, Reports', 15000, 365, '5'),
('Premium Package', 'Full features, Unlimited users, Unlimited medicines, SMS alerts', 35000, 365, 'Unlimited');
