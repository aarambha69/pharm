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
        console.error('Database connection failed:', err);
        process.exit(1);
    }

    // Add qr_image_blob column
    db.query('ALTER TABLE payment_methods ADD COLUMN qr_image_blob LONGBLOB AFTER notes', (err) => {
        if (err && err.code !== 'ER_DUP_FIELDNAME') {
            console.error('Failed to add qr_image_blob:', err.message);
        } else {
            console.log('✅ qr_image_blob column added');
        }

        // Add is_active column
        db.query('ALTER TABLE payment_methods ADD COLUMN is_active BOOLEAN DEFAULT TRUE AFTER qr_image_blob', (err) => {
            if (err && err.code !== 'ER_DUP_FIELDNAME') {
                console.error('Failed to add is_active:', err.message);
            } else {
                console.log('✅ is_active column added');
            }

            console.log('✅ Payment methods schema ready for QR BLOB storage');
            db.end();
        });
    });
});
