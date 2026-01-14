const mysql = require('mysql2');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const db = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASS || '1234',
    database: process.env.DB_NAME || 'PharmacyDB'
});

db.connect((err) => {
    if (err) {
        console.error('DB Connection Failed:', err.message);
        process.exit(1);
    }
    console.log('Connected to DB. Checking columns...');

    const queries = [
        "ALTER TABLE sales ADD COLUMN customer_sex VARCHAR(20) DEFAULT 'Other';",
        "ALTER TABLE sales ADD COLUMN invoice_date DATETIME DEFAULT NULL;"
    ];

    let completed = 0;

    queries.forEach(q => {
        db.query(q, (err) => {
            if (err) {
                if (err.code === 'ER_DUP_FIELDNAME') {
                    console.log('Column already exists (skipped).');
                } else {
                    console.error('Error:', err.message);
                }
            } else {
                console.log('Column added successfully.');
            }
            completed++;
            if (completed === queries.length) {
                console.log('Done.');
                db.end();
            }
        });
    });
});
