const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.query('SHOW CREATE TABLE sales', (err, results) => {
    if (err) console.error(err);
    else console.log(results[0]['Create Table']);
    db.end();
});
