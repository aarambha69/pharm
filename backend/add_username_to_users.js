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
    console.log('Checking users table for username column...');

    db.query("SHOW COLUMNS FROM users LIKE 'username'", (err, results) => {
        if (err) console.error(err);

        if (results.length === 0) {
            console.log('Adding username column...');
            db.query("ALTER TABLE users ADD COLUMN username VARCHAR(50) UNIQUE AFTER name", (err) => {
                if (err) console.error('Error adding column:', err.message);
                else console.log('Username column added successfully.');
                process.exit();
            });
        } else {
            console.log('Username column already exists.');
            process.exit();
        }
    });
});
