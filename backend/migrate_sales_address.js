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

    // Add customer_address to sales
    const alterQuery = "ALTER TABLE sales ADD COLUMN customer_address VARCHAR(255) NULL";

    db.query(alterQuery, (err, result) => {
        if (err) {
            if (err.code === 'ER_DUP_FIELDNAME') {
                console.log('Column customer_address already exists');
            } else {
                console.error('Error adding column:', err);
            }
        } else {
            console.log('Added customer_address to sales table');
        }
        db.end();
    });
});
