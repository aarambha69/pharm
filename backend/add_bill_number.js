const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

const query = 'ALTER TABLE sales ADD COLUMN bill_number VARCHAR(50) UNIQUE AFTER customer_id';

db.query(query, (err, result) => {
    if (err) console.error('Error:', err.message);
    else console.log('Success: bill_number column added');
    db.end();
});
