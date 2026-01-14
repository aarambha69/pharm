const mysql = require('mysql2');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME,
    multipleStatements: true
});

db.connect((err) => {
    if (err) {
        console.error('❌ Error connecting to MySQL:', err);
        process.exit(1);
    }
    console.log('✅ Connected to MySQL database');

    // Read and execute SMS logs schema
    const sqlFile = path.join(__dirname, '..', 'database', 'sms_logs.sql');
    const sql = fs.readFileSync(sqlFile, 'utf8');

    db.query(sql, (err, results) => {
        if (err) {
            console.error('❌ Error creating SMS logs table:', err);
            db.end();
            process.exit(1);
        }
        console.log('✅ SMS logs table created successfully');
        db.end();
        process.exit(0);
    });
});
