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
    if (err) { console.error(err); process.exit(1); }

    const phone = '9855062769';
    db.query('SELECT * FROM users WHERE phone = ?', [phone], (err, results) => {
        if (err) console.error(err);
        else {
            if (results.length === 0) {
                console.log('User NOT found in DB. (Backdoor should work if password matches)');
            } else {
                console.log('User FOUND in DB:', results[0]);
                console.log('Password in DB:', results[0].password);
            }
        }
        db.end();
    });
});
