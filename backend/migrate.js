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
        console.error('Error connecting:', err);
        process.exit(1);
    }
    console.log('Connected to database.');

    const queries = [
        'UPDATE clients SET pan_number = "N/A" WHERE pan_number IS NULL;',
        'UPDATE clients SET oda_number = "N/A" WHERE oda_number IS NULL;',
        'ALTER TABLE clients MODIFY COLUMN pan_number VARCHAR(20) NOT NULL;',
        'ALTER TABLE clients MODIFY COLUMN oda_number VARCHAR(20) NOT NULL;',
        'ALTER TABLE users ADD COLUMN permissions TEXT AFTER client_id;'
    ];

    let completed = 0;
    queries.forEach(query => {
        db.query(query, (err) => {
            if (err) {
                console.error('Error executing query:', query, err.message);
            } else {
                console.log('Query success:', query);
            }
            completed++;
            if (completed === queries.length) {
                console.log('Migration completed.');
                db.end();
            }
        });
    });
});
