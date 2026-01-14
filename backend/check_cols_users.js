const mysql = require('mysql2');
require('dotenv').config({ path: __dirname + '/.env' });

const db = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASS || '1234',
    database: process.env.DB_NAME || 'PharmacyDB'
});

db.connect();

db.query('DESCRIBE users', (err, results) => {
    if (err) {
        console.error(err);
    } else {
        console.table(results);
    }
    db.end();
    process.exit(0);
});
