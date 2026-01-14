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
    db.query('DESCRIBE users', (err, results) => {
        if (err) console.error(err);
        else console.log(results);
        db.end();
    });
});
