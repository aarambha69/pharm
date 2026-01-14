const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME,
    multipleStatements: true
});

const migration = `
ALTER TABLE stocks ADD COLUMN mfg_date DATE AFTER batch_number;
ALTER TABLE purchase_items ADD COLUMN mfg_date DATE AFTER batch_no;
ALTER TABLE purchases MODIFY COLUMN grn_no VARCHAR(50) NULL;
`;

db.connect((err) => {
    if (err) { console.error(err); process.exit(1); }
    db.query(migration, (err) => {
        if (err) {
            if (err.code === 'ER_DUP_FIELDNAME') {
                console.log('Columns already exist. Skipping.');
            } else {
                console.error('Migration failed:', err.message);
            }
        } else {
            console.log('Migration successful: mfg_date added and grn_no refined.');
        }
        db.end();
    });
});
