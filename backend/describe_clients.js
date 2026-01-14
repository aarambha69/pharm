const mysql = require('mysql2');
require('dotenv').config();

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

    db.query('DESCRIBE clients', (err, results) => {
        if (err) {
            console.error('Error describing clients:', err);
        } else {
            console.log('Clients table structure:');
            results.forEach(col => {
                console.log(`${col.Field} - ${col.Type} - ${col.Null} - ${col.Key} - ${col.Default}`);
            });
        }
        db.end();
    });
});
