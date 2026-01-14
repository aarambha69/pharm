const mysql = require('mysql2');
const bcrypt = require('bcrypt');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const db = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASS || '1234',
    database: process.env.DB_NAME || 'PharmacyDB'
});

db.connect(async (err) => {
    if (err) { console.error(err); process.exit(1); }

    const phone = '9855062769';
    const newPass = '123456';
    const hashed = await bcrypt.hash(newPass, 10);

    db.query('UPDATE users SET password = ? WHERE phone = ?', [hashed, phone], (err, result) => {
        if (err) console.error(err);
        else {
            console.log('Password updated successfully to hashed "123456".');
            console.log('Rows matched:', result.message);
        }
        db.end();
    });
});
