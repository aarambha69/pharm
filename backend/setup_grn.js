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

DROP TABLE IF EXISTS purchase_return_items;
DROP TABLE IF EXISTS purchase_returns;
DROP TABLE IF EXISTS purchase_items;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS supplier_ledger;
DROP TABLE IF EXISTS sale_items;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS stocks;
DROP TABLE IF EXISTS medicines;

CREATE TABLE medicines (
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

CREATE TABLE stocks (
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

CREATE TABLE sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    customer_id INT,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    discount_amount DECIMAL(15, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    grand_total DECIMAL(15, 2) DEFAULT 0,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    payment_method ENUM('Cash', 'Card', 'UPI', 'Credit') DEFAULT 'Cash',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE sale_items (
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

CREATE TABLE purchases (
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

CREATE TABLE purchase_items (
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

CREATE TABLE purchase_returns (
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

CREATE TABLE purchase_return_items (
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

CREATE TABLE supplier_ledger (
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

SET FOREIGN_KEY_CHECKS = 1;
`;

db.connect((err) => {
    if (err) { console.error(err); process.exit(1); }
    db.query(schema, (err) => {
        if (err) console.error(err.message);
        else console.log('Final GRN Schema applied successfuly.');
        db.end();
    });
});
