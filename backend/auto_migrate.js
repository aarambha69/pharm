const mysql = require('mysql2');

/**
 * Checks for missing critical columns and adds them if necessary.
 * This ensures the app works on other PCs even if they have an old DB schema.
 * @param {mysql.Connection} db 
 */
function runAutoMigration(db) {
    console.log('🔄 Checking Database Integrity...');

    const fixes = [
        {
            table: 'users',
            column: 'status',
            definition: "ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE'",
            checkQuery: "SHOW COLUMNS FROM users LIKE 'status'",
            alterQuery: "ALTER TABLE users ADD COLUMN status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE'"
        }
    ];

    fixes.forEach(fix => {
        db.query(fix.checkQuery, (err, results) => {
            if (err) {
                console.error(`⚠️ Failed to check column ${fix.column} in ${fix.table}:`, err.message);
                return;
            }

            if (results.length === 0) {
                console.log(`🛠️ Fixing missing column: ${fix.table}.${fix.column}...`);
                db.query(fix.alterQuery, (alterErr) => {
                    if (alterErr) {
                        console.error(`❌ Auto-fix failed for ${fix.table}.${fix.column}:`, alterErr.message);
                    } else {
                        console.log(`✅ Auto-fixed: Added ${fix.column} to ${fix.table}`);
                    }
                });
            } else {
                // console.log(`✅ Integrity OK: ${fix.table}.${fix.column} exists.`);
            }
        });
    });
}

module.exports = runAutoMigration;
