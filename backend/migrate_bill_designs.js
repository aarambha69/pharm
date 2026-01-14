const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.connect((err) => {
    if (err) throw err;
    console.log('Connected to MySQL');

    const createTable = `
    CREATE TABLE IF NOT EXISTS bill_designs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT NOT NULL,
        paper_size VARCHAR(10) DEFAULT 'A4',
        orientation VARCHAR(10) DEFAULT 'PORTRAIT',
        config JSON,
        stamp_image LONGBLOB,
        signature_image LONGBLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY unique_client (client_id)
    )`;

    db.query(createTable, (err, result) => {
        if (err) {
            console.error('Error creating table:', err);
        } else {
            console.log('bill_designs table created/verified');
        }
        db.end();
    });
});
