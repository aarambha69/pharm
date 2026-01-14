const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

const tables = [
    {
        name: 'medicines',
        sql: `CREATE TABLE IF NOT EXISTS medicines (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )`
    },
    {
        name: 'stocks',
        sql: `CREATE TABLE IF NOT EXISTS stocks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id INT NOT NULL,
            medicine_id INT NOT NULL,
            vendor_id INT,
            batch_number VARCHAR(50) NOT NULL,
            expiry_date DATE,
            quantity INT DEFAULT 0,
            purchase_price DECIMAL(10, 2) DEFAULT 0,
            selling_price DECIMAL(10, 2) DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL
        )`
    },
    {
        name: 'sale_items',
        sql: `CREATE TABLE IF NOT EXISTS sale_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT NOT NULL,
            medicine_id INT NOT NULL,
            batch_number VARCHAR(50),
            quantity INT NOT NULL,
            unit_price DECIMAL(10, 2),
            total_price DECIMAL(10, 2),
            FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )`
    }
];

db.connect(async (err) => {
    if (err) { console.error(err); process.exit(1); }

    for (const table of tables) {
        console.log(`Ensuring table ${table.name}...`);
        await new Promise((resolve) => {
            db.query(table.sql, (err) => {
                if (err) console.error(` Error creating ${table.name}:`, err.message);
                else console.log(` Table ${table.name} is ready.`);
                resolve();
            });
        });
    }
    db.end();
});
