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
        console.error('Error connecting:', err);
        process.exit(1);
    }
    console.log('Connected to MySQL');

    const schemaPath = path.join(__dirname, '..', 'database', 'schema.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');

    // Split by semicolon and filter out empty strings
    const queries = schema.split(';').map(q => q.trim()).filter(q => q.length > 0);

    let completed = 0;
    let errors = 0;

    console.log(`Found ${queries.length} queries to execute.`);

    function runQuery(index) {
        if (index >= queries.length) {
            console.log(`Finished with ${errors} errors.`);
            db.end();
            return;
        }

        const query = queries[index];
        db.query(query, (err) => {
            if (err) {
                console.error(`Error in query ${index}:`, err.message);
                errors++;
            } else {
                // console.log(`Query ${index} success.`);
            }
            runQuery(index + 1);
        });
    }

    runQuery(0);
});
