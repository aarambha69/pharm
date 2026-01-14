const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.beginTransaction((err) => {
    if (err) {
        console.error('Transaction error:', err);
        return db.end();
    }

    const queries = [
        'ALTER TABLE sales ADD COLUMN customer_name VARCHAR(255) AFTER bill_number',
        'ALTER TABLE sales ADD COLUMN customer_contact VARCHAR(50) AFTER customer_name',
        'ALTER TABLE sales ADD COLUMN cashier_id INT AFTER customer_contact',
        'ALTER TABLE sales ADD COLUMN user_id INT AFTER cashier_id',
        'ALTER TABLE sales ADD COLUMN status VARCHAR(50) DEFAULT "completed" AFTER transaction_ref'
    ];

    let completed = 0;
    queries.forEach(query => {
        db.query(query, (err) => {
            if (err && !err.message.includes('Duplicate column name')) {
                console.log('Skipping (may already exist):', err.message);
            } else if (!err) {
                console.log('Added column successfully');
            }
            completed++;
            if (completed === queries.length) {
                db.commit((err) => {
                    if (err) console.error('Commit error:', err);
                    else console.log('All columns added/verified');
                    db.end();
                });
            }
        });
    });
});
