const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

const migrationQueries = [
    // Alter vendors table
    {
        desc: "Restructuring vendors table",
        sql: `ALTER TABLE vendors 
              CHANGE COLUMN VendorID id INT AUTO_INCREMENT,
              ADD COLUMN client_id INT NOT NULL AFTER id,
              ADD COLUMN supplier_code VARCHAR(50) AFTER client_id,
              ADD COLUMN company_name VARCHAR(150) AFTER Name,
              ADD COLUMN pan_vat VARCHAR(50) AFTER company_name,
              ADD COLUMN contact_person VARCHAR(100) AFTER pan_vat,
              ADD COLUMN alt_phone VARCHAR(20) AFTER Phone,
              ADD COLUMN email VARCHAR(100) AFTER alt_phone,
              ADD COLUMN status ENUM('Active', 'Inactive') DEFAULT 'Active' AFTER Address,
              ADD COLUMN payment_terms VARCHAR(50) DEFAULT 'Cash' AFTER status,
              ADD COLUMN opening_due DECIMAL(10,2) DEFAULT 0.00 AFTER payment_terms,
              ADD COLUMN current_due DECIMAL(10,2) DEFAULT 0.00 AFTER opening_due,
              ADD COLUMN bank_info TEXT AFTER current_due,
              ADD COLUMN notes TEXT AFTER bank_info,
              ADD COLUMN created_by INT AFTER notes,
              ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`
    },
    {
        desc: "Adding unique constraint to vendors",
        sql: `ALTER TABLE vendors ADD CONSTRAINT unique_vendor_per_client UNIQUE (client_id, Name)`
    },
    // Create vendor_payments table
    {
        desc: "Creating vendor_payments table",
        sql: `CREATE TABLE IF NOT EXISTS vendor_payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_id INT NOT NULL,
                vendor_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_date DATE NOT NULL,
                method ENUM('Cash', 'Bank', 'Wallet', 'Other') DEFAULT 'Cash',
                reference_no VARCHAR(100),
                notes TEXT,
                created_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
              )`
    }
];

db.connect(async (err) => {
    if (err) {
        console.error('Connection failed:', err);
        process.exit(1);
    }

    for (const q of migrationQueries) {
        console.log(`Executing: ${q.desc}...`);
        try {
            await new Promise((resolve, reject) => {
                db.query(q.sql, (err) => {
                    if (err) {
                        if (err.code === 'ER_DUP_FIELDNAME' || err.code === 'ER_PKEY_COLUMN_DLL' || err.code === 'ER_MULTIPLE_PRI_KEY' || err.code === 'ER_DUP_KEYNAME') {
                            console.log(`  Row/Constraint already exists, skipping.`);
                            resolve();
                        } else {
                            reject(err);
                        }
                    } else {
                        resolve();
                    }
                });
            });
        } catch (err) {
            console.error(`  Error in ${q.desc}:`, err.message);
        }
    }

    console.log('Migration completed.');
    db.end();
    process.exit(0);
});
