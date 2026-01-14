const mysql = require('mysql2');
require('dotenv').config({ path: '../backend/.env' });

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.connect((err) => {
    if (err) {
        console.error('Error connecting to MySQL:', err);
        process.exit(1);
    }
    console.log('Connected to MySQL');

    db.query('SHOW TABLES', (err, results) => {
        if (err) {
            console.error('Error showing tables:', err);
        } else {
            console.log('Tables:', results);
        }

        db.query('SELECT * FROM packages', (err, results) => {
            if (err) console.error('Error selecting packages:', err);
            else console.log('Packages:', results);

            db.query('SELECT * FROM clients', (err, results) => {
                if (err) console.error('Error selecting clients:', err);
                else console.log('Clients:', results);
                db.end();
            });
        });
    });
});
