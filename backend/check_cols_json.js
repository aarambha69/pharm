const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.query('SELECT * FROM sales LIMIT 1', (err, results, fields) => {
    if (err) console.error(err);
    else {
        const cols = fields.map(f => f.name);
        console.log(JSON.stringify(cols));
    }
    db.end();
});
