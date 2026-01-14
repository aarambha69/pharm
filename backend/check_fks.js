const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

const sql = `
SELECT TABLE_NAME, CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME 
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE REFERENCED_TABLE_SCHEMA = ? AND (REFERENCED_TABLE_NAME = 'medicines' OR REFERENCED_TABLE_NAME = 'stocks')
`;

db.connect((err) => {
    if (err) { console.error(err); process.exit(1); }
    db.query(sql, [process.env.DB_NAME], (err, res) => {
        if (err) console.error(err);
        else console.log(res);
        db.end();
    });
});
