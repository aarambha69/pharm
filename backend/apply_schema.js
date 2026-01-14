const mysql = require('mysql2');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    multipleStatements: true
});

db.connect((err) => {
    if (err) {
        console.error('Error connecting:', err);
        process.exit(1);
    }
    console.log('Connected to MySQL');

    const schemaPath = path.join(__dirname, '..', 'database', 'schema.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');

    db.query(schema, (err, results) => {
        if (err) {
            console.error('Error applying schema:', err);
        } else {
            console.log('Schema applied successfully');
        }

        // Also apply device activation table if it exists
        try {
            const devPath = path.join(__dirname, '..', 'database', 'device_activation.sql');
            if (fs.existsSync(devPath)) {
                const devSchema = fs.readFileSync(devPath, 'utf8');
                db.query(devSchema, (err) => {
                    if (err) console.error('Error applying device activation schema:', err);
                    else console.log('Device activation schema applied');
                    db.end();
                });
            } else {
                db.end();
            }
        } catch (e) {
            db.end();
        }
    });
});
