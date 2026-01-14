const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

const queries = [
    `CREATE TABLE IF NOT EXISTS sms_queue (
        id INT AUTO_INCREMENT PRIMARY KEY,
        to_number VARCHAR(20) NOT NULL,
        message_text TEXT NOT NULL,
        status ENUM('pending', 'failed', 'sent') DEFAULT 'pending',
        retry_count INT DEFAULT 0,
        last_retry TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`,
    `CREATE TABLE IF NOT EXISTS sms_logs (
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
    )`
];

db.connect(async (err) => {
    if (err) {
        console.error('Connection failed:', err);
        process.exit(1);
    }
    console.log('Connected to DB');

    for (const query of queries) {
        await new Promise(resolve => {
            db.query(query, (err) => {
                if (err) console.error('Query failed:', err.message);
                else console.log('Table ensured.');
                resolve();
            });
        });
    }
    db.end();
    process.exit(0);
});
