const mysql = require('mysql2');
require('dotenv').config({ path: __dirname + '/.env' }); // Ensure .env is loaded

const db = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASS || '1234',
    database: process.env.DB_NAME || 'PharmacyDB'
});

db.connect((err) => {
    if (err) {
        console.error('Connection Failed:', err.message);
        process.exit(1);
    }
    console.log('Connected to MySQL. Fixing schema...');

    const query = "ALTER TABLE users ADD COLUMN status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE'";

    db.query(query, (err, result) => {
        if (err) {
            if (err.code === 'ER_DUP_FIELDNAME') {
                console.log('✅ Column "status" already exists. No changes needed.');
            } else {
                console.error('❌ Failed to add column:', err.message);
                process.exit(1);
            }
        } else {
            console.log('✅ Successfully added "status" column to users table.');
        }
        db.end();
        process.exit(0);
    });
});
