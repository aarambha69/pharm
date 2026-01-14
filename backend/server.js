const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const bodyParser = require('body-parser');
const jwt = require('jsonwebtoken');
require('dotenv').config();
const purchaseRoutes = require('./purchase_routes');
const dashboardRoutes = require('./dashboard_routes');
const billDesignRoutes = require('./bill_design_routes');
const paymentMethodsRoutes = require('./payment_methods_routes');
const superBillDesignRoutes = require('./super_bill_design_routes');
const smsAlertRoutes = require('./sms_alert_routes');
const SMSAlertScheduler = require('./sms_scheduler');
const customerRoutes = require('./customer_routes');
const notificationRoutes = require('./notification_routes');
const refundRoutes = require('./refund_routes');
const karobarRoutes = require('./karobar_routes');
const usersRoutes = require('./users_routes');

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: '200mb' }));
app.use(bodyParser.urlencoded({ limit: '200mb', extended: true }));
app.use('/uploads', express.static('uploads'));

const multer = require('multer');
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, 'uploads/')
    },
    filename: function (req, file, cb) {
        cb(null, Date.now() + '-' + file.originalname)
    }
});
const upload = multer({ storage: storage });


app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    next();
});

// --- GLOBAL EXCEPTION HANDLERS (ZERO CRASH POLICY) ---
process.on('uncaughtException', (err) => {
    console.error('CRITICAL: Uncaught Exception:', err);
    // Log to file if needed (fs.appendFile...)
    // Do NOT exit, try to keep running as per "Zero Crash" rule, unless state is corrupted.
    // For a desktop app backend, resilience is prioritized.
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('CRITICAL: Unhandled Rejection at:', promise, 'reason:', reason);
});
// -----------------------------------------------------

// --- DEVICE ACTIVATION & LICENSING (NO AUTH) ---

app.post('/api/check-license', (req, res) => {
    const { machine_id } = req.body;
    console.log(`License check for: ${machine_id}`);
    const query = 'SELECT * FROM device_activations WHERE machine_id = ? AND status = "active"';
    db.query(query, [machine_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length > 0) {
            const activation = results[0];
            return res.json({
                valid: true,
                role: activation.user_role,
                package_name: 'Premium',
                features: 'inventory,billing,crm,reports,users,vendors,announcements,settings,karobar',
                expiry: '2099-12-31'
            });
        }
        res.json({ valid: false, message: 'Device not activated' });
    });
});

app.post('/api/activate-system', (req, res) => {
    const { machine_id, license_key, role, client_id } = req.body;
    const insertQuery = 'INSERT INTO device_activations (machine_id, user_role, client_id, activated_at, status) VALUES (?, ?, ?, NOW(), "active") ON DUPLICATE KEY UPDATE status="active", user_role=?, client_id=?';
    db.query(insertQuery, [machine_id, role, client_id, role, client_id], (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Activation successful' });
    });
});



const path = require('path');
// Explicitly load .env from the same directory as server.js
require('dotenv').config({ path: path.join(__dirname, '.env') });

const {
    sendSMS, sendWelcomeSMS, sendPasswordResetSMS,
    sendLowStockAlert, sendExpiryAlert, sendBulkSMS,
    getSMSBalance
} = require('./services/sms');

const db = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    // Fallback to '1234' if DB_PASS is undefined OR empty string
    password: process.env.DB_PASS || '1234',
    database: process.env.DB_NAME || 'PharmacyDB',
    connectTimeout: 10000 // 10 seconds timeout
});

console.log('Attempting to connect to MySQL...');
console.log('Host:', process.env.DB_HOST || '127.0.0.1 (Default)');
console.log('User:', process.env.DB_USER || 'root (Default)');
console.log('Pass:', process.env.DB_PASS ? '******' : '1234 (Fallback)');

db.connect((err) => {
    if (err) {
        console.error('----------------------------------------');
        console.error('CRITICAL DATABASE ERROR:');
        console.error(err.code);
        console.error(err.message);
        console.error('----------------------------------------');
        return;
    }
    console.log('----------------------------------------');
    console.log('✅ SUCCESS: Connected to MySQL database');
    console.log('----------------------------------------');

    // Initialize SMS Offline Queue
    require('./services/sms').setDB(db);

    // Run Auto-Migration (Self-Healing)
    const runAutoMigration = require('./auto_migrate');
    runAutoMigration(db);
});

app.set('db', db); // Make DB accessible to routes

// --- PUBLIC ROUTES (NO AUTH REQUIRED) ---

// Login Route
app.post('/api/login', (req, res) => {
    const { phone, password } = req.body;
    console.log('Login attempt:', phone, password ? '******' : '(none)'); // DEBUG: Don't log checks

    // 1. Fetch user by phone first (don't check password in SQL)
    const query = 'SELECT u.*, c.pharmacy_name, c.status as client_status, c.license_expiry, c.oda_number, c.pan_number, c.address as pharmacy_address, c.contact_number as pharmacy_contact FROM users u LEFT JOIN clients c ON u.client_id = c.id WHERE u.phone = ?';

    db.query(query, [phone], async (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        // 2. Check hardcoded super admin backdoor if not found in DB
        if (results.length === 0) {
            if (phone === '9855062769' && (password === '987654321' || password === '123456')) {
                const token = jwt.sign({ id: 0, phone, role: 'SUPER_ADMIN', client_id: 1 }, process.env.JWT_SECRET);
                return res.json({ token, user: { id: 0, name: 'Aarambha Aryal', role: 'SUPER_ADMIN', phone: '9855062769', client_id: 1 } });
            }
            return res.status(401).json({ message: 'Invalid credentials' });
        }

        const user = results[0];
        let passwordMatch = false;

        // 3. Verify Password (Hash vs Plain Text)
        try {
            // First try bcrypt compare
            const isMatch = await bcrypt.compare(password, user.password);
            if (isMatch) {
                passwordMatch = true;
            } else {
                // FALLBACK: Check plain text (for old users)
                if (password === user.password) {
                    passwordMatch = true;
                    // Optional: Upgrade to hash for next time? 
                    // For now, let's just allow it to keep logic simple & safe.
                    // Ideally: db.query('UPDATE users SET password = ? ...', [hashed])
                }
            }
        } catch (e) {
            // If bcrypt errors (e.g. data in DB isn't a hash), try plain text
            if (password === user.password) {
                passwordMatch = true;
            }
        }

        if (!passwordMatch) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }

        // 4. Strict Expiry & Status Check
        if (user.role !== 'SUPER_ADMIN' && user.client_id) {
            if (user.client_status !== 'active') {
                return res.status(403).json({ message: 'Client account is inactive' });
            }
            if (user.license_expiry && new Date(user.license_expiry) < new Date()) {
                const expiryDate = new Date(user.license_expiry).toLocaleDateString();
                return res.status(403).json({
                    message: `Subscription Expired on ${expiryDate}. Contact Support.`
                });
            }
        }

        const token = jwt.sign({ id: user.id, phone: user.phone, role: user.role, client_id: user.client_id }, process.env.JWT_SECRET);
        res.json({
            token,
            user: {
                id: user.id, name: user.name, phone: user.phone, role: user.role, client_id: user.client_id,
                pharmacy_name: user.pharmacy_name || 'System', profile_pic: user.profile_pic,
                oda_number: user.oda_number, pan_number: user.pan_number, address: user.pharmacy_address,
                permissions: user.permissions
            }
        });
    });
});

// --- LICENSE & ACTIVATION ROUTES ---

// Check License Status
app.post('/api/check-license', (req, res) => {
    const { machine_id } = req.body;

    // Check if machine exists in licenses

    // --- SPECIAL WHITELIST FOR USER DEVICE ---
    // UUID provided: 91DE6E66-1ADA-EF11-A4FE-38A746181EA0
    if (machine_id && machine_id.toUpperCase().includes('91DE6E66-1ADA-EF11-A4FE-38A746181EA0')) {
        return res.json({
            valid: true,
            role: 'SUPER_ADMIN',
            package_name: 'Ultimate Enterprise',
            features: 'All Features Unlocked',
            expiry: '2099-12-31T23:59:59.000Z'
        });
    }
    // ------------------------------------------

    const query = `
        SELECT l.*, c.pharmacy_name, p.name as package_name, p.features 
        FROM licenses l
        LEFT JOIN clients c ON l.client_id = c.id
        LEFT JOIN packages p ON c.package_id = p.id
        WHERE l.machine_id = ?
    `;

    db.query(query, [machine_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        if (results.length > 0) {
            const license = results[0];
            // Check expiry
            const now = new Date();
            const expiry = new Date(license.valid_until);

            if (license.status === 'active' && expiry > now) {
                return res.json({
                    valid: true,
                    role: 'ADMIN', // Default role for licensed machine
                    package_name: license.package_name,
                    features: license.features,
                    expiry: license.valid_until
                });
            }
        }
        res.json({ valid: false });
    });
});

// Super Admin Manual Device Activation
app.post('/api/activate-super-admin', (req, res) => {
    const { machine_id, phone, password } = req.body;

    // --- MASTER KEY BYPASS (Avoids DB Read Hangs) ---
    // User requested bypass for 9855062769
    if (phone === '9855062769' && (password === '987654321' || password === '123456')) {
        // Skip user lookup, go straight to activation
        activateMachine(res, machine_id);
        return;
    }
    // ------------------------------------------------

    // 1. Verify Super Admin Creds
    const authQuery = 'SELECT * FROM users WHERE phone = ? AND password = ? AND role = "SUPER_ADMIN"';

    db.query(authQuery, [phone, password], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        if (results.length === 0) {
            // Also check root/fallback creds
            if (phone === '9855062769' && (password === '987654321' || password === '123456')) {
                // Pass
            } else {
                return res.status(401).json({ message: 'Invalid Super Admin Credentials' });
            }
        }

        // 2. Activate Machine (Upsert)
        const expiryDate = new Date();
        expiryDate.setFullYear(expiryDate.getFullYear() + 10); // 10 Years Validity

        // client_id 1 is usually the default/super admin client
        const upsertQuery = `
            INSERT INTO licenses (client_id, machine_id, license_key, valid_from, valid_until, status)
            VALUES (1, ?, 'SUPER-ADMIN-DEVICE', NOW(), ?, 'active')
            ON DUPLICATE KEY UPDATE 
            status='active', valid_until=?, client_id=1
        `;

        db.query(upsertQuery, [machine_id, expiryDate, expiryDate], (err2, res2) => {
            if (err2) return res.status(500).json({ error: err2.message });
            res.json({ success: true, message: 'Device Authorized Permanently' });
        });
    });
});

function activateMachine(res, machine_id) {
    const expiryDate = new Date();
    expiryDate.setFullYear(expiryDate.getFullYear() + 10); // 10 Years Validity

    const upsertQuery = `
        INSERT INTO licenses (client_id, machine_id, license_key, valid_from, valid_until, status)
        VALUES (1, ?, 'SUPER-ADMIN-DEVICE', NOW(), ?, 'active')
        ON DUPLICATE KEY UPDATE 
        status='active', valid_until=?, client_id=1
    `;

    db.query(upsertQuery, [machine_id, expiryDate, expiryDate], (err2, res2) => {
        if (err2) return res.status(500).json({ error: err2.message });
        res.json({ success: true, message: 'Device Authorized Permanently' });
    });
}

// Authentication Middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    if (!authHeader) return res.sendStatus(401);
    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') return res.sendStatus(401);
    const token = parts[1];
    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
};

// --- AUTHENTICATED ROUTES ---
// --- AUTHENTICATED ROUTES ---
app.use('/api', authenticateToken, purchaseRoutes);
app.use('/api', authenticateToken, paymentMethodsRoutes);
app.use('/api', authenticateToken, dashboardRoutes);
app.use('/api', authenticateToken, billDesignRoutes);
app.use('/api', authenticateToken, superBillDesignRoutes);
app.use('/api', authenticateToken, smsAlertRoutes);
app.use('/api', authenticateToken, customerRoutes);
app.use('/api', authenticateToken, notificationRoutes);
app.use('/api', authenticateToken, refundRoutes);
app.use('/api/users', authenticateToken, usersRoutes);

// Profile Management
app.get('/api/profile', authenticateToken, (req, res) => {
    const userId = req.user.id;
    if (!userId) {
        return res.json({ name: 'Aarambha Aryal', role: 'SUPER_ADMIN', phone: '9855062769', profile_pic: null });
    }
    db.query('SELECT name, phone, email, role, profile_pic, permissions FROM users WHERE id = ?', [userId], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'User not found' });
        res.json(results[0]);
    });
});

app.post('/api/profile', authenticateToken, (req, res) => {
    const userId = req.user.id;
    const { name, email, phone, profile_pic } = req.body;

    console.log('Profile Update Request:', {
        userId,
        name,
        email,
        phone,
        profile_pic_length: profile_pic ? profile_pic.length : 0
    });

    // If no userId (hardcoded account), just return success without updating DB
    if (!userId) {
        console.log('Hardcoded account - profile updated in memory only');
        return res.json({ message: 'Profile updated' });
    }

    db.query('UPDATE users SET name = ?, email = ?, phone = ?, profile_pic = ? WHERE id = ?',
        [name, email, phone, profile_pic, userId], (err) => {
            if (err) {
                console.error('Profile update error:', err);
                return res.status(500).json({ error: err.message, details: err.sqlMessage });
            }
            console.log('Profile updated successfully for user:', userId);
            res.json({ message: 'Profile updated' });
        });
});

// --- SUPER ADMIN ROUTES ---

// Get all clients with design status
app.get('/api/super/clients', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const query = `
        SELECT c.*, p.name as package_name, 
               (SELECT permissions FROM users WHERE client_id = c.id AND role = 'ADMIN' LIMIT 1) as permissions
        FROM clients c 
        LEFT JOIN packages p ON c.package_id = p.id 
        GROUP BY c.id
    `;
    db.query(query, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Get system audit logs
app.get('/api/super/audit-logs', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const query = 'SELECT al.*, u.name as user_name FROM audit_logs al LEFT JOIN users u ON al.user_id = u.id ORDER BY al.created_at DESC LIMIT 100';
    db.query(query, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Get System Settings
app.get('/api/super/settings', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    db.query('SELECT * FROM system_settings', (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Update System Settings
app.post('/api/super/settings', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const settings = req.body; // Expecting an object { key: value }

    const queries = Object.entries(settings).map(([key, value]) => {
        return new Promise((resolve, reject) => {
            db.query('UPDATE system_settings SET config_value = ? WHERE config_key = ?', [value, key], (err) => {
                if (err) reject(err);
                else resolve();
            });
        });
    });

    Promise.all(queries)
        .then(() => res.json({ message: 'Settings updated successfully' }))
        .catch(err => res.status(500).json({ error: err.message }));
});

// Get Announcements
app.get('/api/super/announcements', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    db.query('SELECT * FROM announcements ORDER BY created_at DESC', (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Create Announcement
app.post('/api/super/announcements', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { title, message, target_role, target_client_id, expiry_date } = req.body;
    db.query('INSERT INTO announcements (title, message, target_role, target_client_id, expiry_date) VALUES (?, ?, ?, ?, ?)',
        [title, message, target_role || 'ALL', target_client_id || null, expiry_date || null], (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ message: 'Announcement broadcasted successfully' });
        });
});

// --- SUPER ADMIN REPORTING ENDPOINTS ---

// 1. Sales Report (Summary of all bills)
app.get('/api/super/reports/sales', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { client_id, start_date, end_date } = req.query;

    let query = `
        SELECT s.*, c.pharmacy_name, u.name as cashier_name 
        FROM sales s 
        JOIN clients c ON s.client_id = c.id 
        JOIN users u ON s.cashier_id = u.id 
        WHERE 1=1
    `;
    const params = [];

    if (client_id && client_id !== 'all') {
        query += ' AND s.client_id = ?';
        params.push(client_id);
    }
    if (start_date) {
        query += ' AND DATE(s.created_at) >= ?';
        params.push(start_date);
    }
    if (end_date) {
        query += ' AND DATE(s.created_at) <= ?';
        params.push(end_date);
    }

    query += ' ORDER BY s.created_at DESC';

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// 2. Item-wise Sales Report
app.get('/api/super/reports/item-wise', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { client_id, start_date, end_date } = req.query;

    let query = `
        SELECT si.*, m.name as medicine_name, s.bill_number, s.created_at, c.pharmacy_name 
        FROM sale_items si 
        JOIN sales s ON si.sale_id = s.id 
        JOIN medicines m ON si.medicine_id = m.id 
        JOIN clients c ON s.client_id = c.id 
        WHERE 1=1
    `;
    const params = [];

    if (client_id && client_id !== 'all') {
        query += ' AND s.client_id = ?';
        params.push(client_id);
    }
    if (start_date) {
        query += ' AND DATE(s.created_at) >= ?';
        params.push(start_date);
    }
    if (end_date) {
        query += ' AND DATE(s.created_at) <= ?';
        params.push(end_date);
    }

    query += ' ORDER BY s.created_at DESC';

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// 3. Top Selling Products
app.get('/api/super/reports/top-selling', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { client_id, limit = 10 } = req.query;

    let query = `
        SELECT m.name, SUM(si.quantity) as total_sold, SUM(si.total_price) as total_revenue, c.pharmacy_name 
        FROM sale_items si 
        JOIN medicines m ON si.medicine_id = m.id 
        JOIN sales s ON si.sale_id = s.id 
        JOIN clients c ON s.client_id = c.id 
        WHERE 1=1
    `;
    const params = [];

    if (client_id && client_id !== 'all') {
        query += ' AND s.client_id = ?';
        params.push(client_id);
    }

    query += ' GROUP BY si.medicine_id, s.client_id ORDER BY total_sold DESC LIMIT ?';
    params.push(parseInt(limit));

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Impersonation: Login as specific Client Admin
app.post('/api/super/login-as-admin', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { client_id } = req.body;

    const query = 'SELECT u.*, c.pharmacy_name FROM users u JOIN clients c ON u.client_id = c.id WHERE u.client_id = ? AND u.role = "ADMIN" LIMIT 1';
    db.query(query, [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'No admin user found for this client' });

        const user = results[0];
        const token = jwt.sign({ id: user.id, phone: user.phone, role: user.role, client_id: user.client_id }, process.env.JWT_SECRET);

        // Log the impersonation
        db.query('INSERT INTO audit_logs (action, user_id, details) VALUES (?, ?, ?)',
            ['IMPERSONATION', req.user.id, `Impersonated Pharmacy: ${user.pharmacy_name}`]);

        res.json({ token, user: { id: user.id, name: user.name, role: user.role, pharmacy_name: user.pharmacy_name, client_id: user.client_id } });
    });
});

// Create Client with Admin User
app.post('/api/super/clients', authenticateToken, upload.fields([{ name: 'logo' }, { name: 'owner_photo' }]), (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const {
        pharmacy_name, address, pan_number, dda_number, oda_number,
        contact_number, package_id, duration_days, admin_name,
        admin_phone, admin_password, client_id_code, permissions
    } = req.body;

    const final_client_code = client_id_code || ('CL' + Date.now());

    let expiry_date;
    if (req.body.expiry_date) {
        expiry_date = new Date(req.body.expiry_date);
    } else {
        const durationCount = parseInt(duration_days) || 365;
        expiry_date = new Date();
        expiry_date.setDate(expiry_date.getDate() + durationCount);
    }

    const logo_path = req.files['logo'] ? `uploads/${req.files['logo'][0].filename}` : null;
    const owner_photo_path = req.files['owner_photo'] ? `uploads/${req.files['owner_photo'][0].filename}` : null;

    // Start transaction
    db.beginTransaction((err) => {
        if (err) return res.status(500).json({ error: err.message });

        // Insert client
        const clientQuery = `
            INSERT INTO clients 
            (pharmacy_name, address, pan_number, dda_number, oda_number, logo_path, owner_photo_path, contact_number, client_id_code, package_id, license_expiry, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "active")
        `;
        db.query(clientQuery, [
            pharmacy_name, address, pan_number || null, dda_number || null, oda_number || null,
            logo_path, owner_photo_path, contact_number, final_client_code,
            package_id || 1, expiry_date
        ], (err, clientResult) => {
            if (err) {
                return db.rollback(() => res.status(500).json({ error: err.message }));
            }

            const clientId = clientResult.insertId;

            // Create admin user for this client
            const userQuery = 'INSERT INTO users (phone, password, email, name, role, client_id, permissions) VALUES (?, ?, ?, ?, "ADMIN", ?, ?)';
            db.query(userQuery, [admin_phone, admin_password, '', admin_name, clientId, permissions || null], (err, userResult) => {
                if (err) {
                    return db.rollback(() => res.status(500).json({ error: err.message }));
                }

                // Audit Log
                const auditQuery = 'INSERT INTO audit_logs (action, user_id, details) VALUES ("CREATE_CLIENT", ?, ?)';
                db.query(auditQuery, [req.user.id || 0, `Created Client ID: ${final_client_code}, Pharmacy: ${pharmacy_name}`]);

                db.commit(async (err) => {
                    if (err) {
                        return db.rollback(() => res.status(500).json({ error: err.message }));
                    }

                    // Send SMS with Credentials
                    try {
                        const smsMsg = `[Aarambha PMS] Welcome ${pharmacy_name}! Your account is ready. Client Code: ${final_client_code}, Username: ${admin_phone}, Password: ${admin_password}. Keep it safe.`;
                        await sendSMS(admin_phone, smsMsg);
                    } catch (smsErr) {
                        console.error('Failed to send welcome SMS:', smsErr);
                    }

                    res.json({
                        message: 'Client and admin user created successfully. Credentials sent via SMS.',
                        client_id: clientId,
                        client_code: final_client_code,
                        admin_phone: admin_phone
                    });
                });
            });
        });
    });
});

// Update Client
app.put('/api/super/clients/:id', authenticateToken, upload.fields([{ name: 'logo' }, { name: 'owner_photo' }]), (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { pharmacy_name, address, pan_number, dda_number, oda_number, contact_number, package_id, status, permissions } = req.body;
    const clientId = req.params.id;

    let updateFields = 'pharmacy_name=?, address=?, pan_number=?, dda_number=?, oda_number=?, contact_number=?, package_id=?, status=?';
    let params = [pharmacy_name, address, pan_number, dda_number, oda_number, contact_number, package_id, status];

    if (req.files['logo']) {
        updateFields += ', logo_path=?';
        params.push(`uploads/${req.files['logo'][0].filename}`);
    }
    if (req.files['owner_photo']) {
        updateFields += ', owner_photo_path=?';
        params.push(`uploads/${req.files['owner_photo'][0].filename}`);
    }

    params.push(clientId);

    const query = `UPDATE clients SET ${updateFields} WHERE id=?`;
    db.beginTransaction((err) => {
        if (err) return res.status(500).json({ error: err.message });

        db.query(query, params, (err, result) => {
            if (err) return db.rollback(() => res.status(500).json({ error: err.message }));

            // Update admin permissions if provided
            if (permissions !== undefined) {
                db.query('UPDATE users SET permissions = ? WHERE client_id = ? AND role = "ADMIN"', [permissions, clientId], (err) => {
                    if (err) return db.rollback(() => res.status(500).json({ error: err.message }));
                    finalize();
                });
            } else {
                finalize();
            }

            function finalize() {
                // Audit Log
                const auditQuery = 'INSERT INTO audit_logs (action, user_id, details) VALUES ("UPDATE_CLIENT", ?, ?)';
                db.query(auditQuery, [req.user.id, `Updated Client ID: ${clientId}`], (err) => {
                    db.commit((err) => {
                        if (err) return db.rollback(() => res.status(500).json({ error: err.message }));
                        res.json({ message: 'Client updated successfully' });
                    });
                });
            }
        });
    });
});

// Delete Client
app.delete('/api/super/clients/:id', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const clientId = req.params.id;

    db.query('DELETE FROM clients WHERE id = ?', [clientId], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });

        // Audit Log
        const auditQuery = 'INSERT INTO audit_logs (action, user_id, details) VALUES ("DELETE_CLIENT", ?, ?)';
        db.query(auditQuery, [req.user.id, `Deleted Client ID: ${clientId}`]);

        res.json({ message: 'Client deleted successfully' });
    });
});

// --- LICENSE & ACTIVATION LOGIC ---
const LICENSE_SECRET = 'AARAMBHA_PRO_SECURE_2026';
const crypto = require('crypto');

function generateHashedKey(machine_id, role, client_id) {
    const raw = `${machine_id}-${role}-${client_id || 'SYSTEM'}-${LICENSE_SECRET}`;
    return crypto.createHash('sha256').update(raw).digest('hex').substring(0, 16).toUpperCase();
}

// Generate License Key for a Machine
app.post('/api/super/generate-key', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { machine_id, client_id, role } = req.body;

    if (!machine_id || !role) return res.status(400).json({ error: 'Machine ID and Role required' });

    const key = generateHashedKey(machine_id, role, client_id);

    // Filter to audit logs
    db.query('INSERT INTO audit_logs (action, user_id, details) VALUES (?, ?, ?)',
        ['GENERATE_KEY', req.user.id, `Key for Machine: ${machine_id}, Role: ${role}`]);

    res.json({ key });
});

// Get Super Admin Stats (Enhanced God View)
app.get('/api/super/stats', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const stats_query = `
        SELECT 
            (SELECT COUNT(*) FROM clients) as total_clients,
            (SELECT COUNT(*) FROM clients WHERE status = 'active') as active_licenses,
            (SELECT COUNT(*) FROM clients WHERE license_expiry <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) AND status = 'active') as expiring_soon,
            (SELECT IFNULL(SUM(amount), 0) FROM subscription_invoices WHERE status = 'paid') as total_revenue,
            (SELECT COUNT(*) FROM clients WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)) as new_signups
    `;

    db.query(stats_query, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results[0]);
    });
});

// Get All Packages
app.get('/api/super/packages', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const query = 'SELECT * FROM packages ORDER BY id';
    db.query(query, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Create Package
app.post('/api/super/packages', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const { name, description, price, features, max_users } = req.body;

    const query = 'INSERT INTO packages (name, description, price, features, max_users) VALUES (?, ?, ?, ?, ?)';
    db.query(query, [name, description, price, features, max_users || 'Unlimited'], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Package created successfully', id: result.insertId });
    });
});

// Update Activation Status (Suspend/Revoke/Extend)
app.post('/api/super/license-action', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const { machine_id, action, days } = req.body;

    // Log the action
    const logQuery = 'INSERT INTO audit_logs (action, user_id, details) VALUES (?, ?, ?)';
    const details = `Machine: ${machine_id}${days ? `, Period: ${days} days` : ''}`;
    db.query(logQuery, [action.toUpperCase(), req.user.id, details]);

    if (action === 'extend') {
        const query = 'UPDATE clients c JOIN device_activations da ON c.id = da.client_id SET c.license_expiry = DATE_ADD(c.license_expiry, INTERVAL ? DAY) WHERE da.machine_id = ?';
        db.query(query, [days || 30, machine_id], (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ message: 'License extended successfully' });
        });
    } else {
        const query = 'UPDATE device_activations SET status = ? WHERE machine_id = ?';
        db.query(query, [action, machine_id], (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ message: `License ${action}ed successfully` });
        });
    }
});

// Delete Package
app.delete('/api/super/packages/:id', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const { id } = req.params;

    const query = 'DELETE FROM packages WHERE id = ?';
    db.query(query, [id], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Package deleted successfully' });
    });
});

// Search Clients
app.get('/api/super/clients/search', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const { query } = req.query;
    if (!query) {
        return res.status(400).json({ error: 'Search query is required' });
    }

    const searchQuery = `
        SELECT c.*, p.name as package_name 
        FROM clients c 
        LEFT JOIN packages p ON c.package_id = p.id
        WHERE c.pharmacy_name LIKE ? 
           OR c.contact_number LIKE ? 
           OR c.client_id_code LIKE ?
           OR c.address LIKE ?
           OR c.dda_number LIKE ?
    `;
    const term = `%${query}%`;
    db.query(searchQuery, [term, term, term, term, term], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Global Monitoring (Super Admin view of alerts across all clients)
app.get('/api/check-low-stock', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { client_id } = req.query;

    let query = `
        SELECT c.pharmacy_name, m.name, m.stock_quantity, m.min_stock_level 
        FROM medicines m 
        JOIN clients c ON m.client_id = c.id 
        WHERE m.stock_quantity <= m.min_stock_level
    `;
    const params = [];
    if (client_id && client_id !== 'all') {
        query += ' AND c.id = ?';
        params.push(client_id);
    }

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

app.get('/api/check-expiry', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { client_id } = req.query;

    let query = `
        SELECT c.pharmacy_name, m.name, m.batch_number, m.expiry_date 
        FROM medicines m 
        JOIN clients c ON m.client_id = c.id 
        WHERE m.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 90 DAY)
    `;
    const params = [];
    if (client_id && client_id !== 'all') {
        query += ' AND c.id = ?';
        params.push(client_id);
    }

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Get All Clients
app.get('/api/super/clients', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const query = 'SELECT c.*, p.name as package_name FROM clients c LEFT JOIN packages p ON c.package_id = p.id';
    db.query(query, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Check Device Activation (for desktop app startup)
app.post('/api/check-license', (req, res) => {
    const { machine_id } = req.body;

    if (!machine_id) {
        return res.status(400).json({ valid: false, message: 'Machine ID required' });
    }

    // Check if this device is activated
    const query = 'SELECT da.*, c.license_expiry, c.status as client_status, p.features as package_features, p.name as package_name FROM device_activations da LEFT JOIN clients c ON da.client_id = c.id LEFT JOIN packages p ON c.package_id = p.id WHERE da.machine_id = ?';
    db.query(query, [machine_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        if (results.length > 0) {
            const activation = results[0];

            // Check if license is suspended or revoked
            if (activation.status !== 'active' && !activation.is_permanent) {
                return res.json({ valid: false, message: `License is ${activation.status}` });
            }

            // If it's a permanent activation (Super Admin), always valid
            if (activation.is_permanent) {
                return res.json({ valid: true, role: activation.user_role, permanent: true });
            }

            // For client devices, check license expiry
            if (activation.client_id) {
                const isExpired = new Date(activation.license_expiry) < new Date();

                if (activation.client_status === 'active' && !isExpired) {
                    return res.json({
                        valid: true,
                        role: activation.user_role,
                        package_name: activation.package_name,
                        features: activation.package_features,
                        expiry: activation.license_expiry
                    });
                } else {
                    return res.json({ valid: false, message: isExpired ? 'License expired' : 'Client account inactive' });
                }
            } else {
                return res.json({ valid: true, role: activation.user_role });
            }
        } else {
            return res.json({ valid: false, message: 'Device not activated' });
        }
    });
});

// Activate Device (Super Admin activates a device permanently, or client activation)
app.post('/api/activate-device', authenticateToken, (req, res) => {
    const { machine_id, role, client_id, permanent } = req.body;

    // Only Super Admin can activate devices
    if (req.user.role !== 'SUPER_ADMIN') {
        return res.sendStatus(403);
    }

    const isPermanent = permanent || role === 'SUPER_ADMIN';

    const query = 'INSERT INTO device_activations (machine_id, user_role, client_id, activated_by, is_permanent) VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE user_role = ?, client_id = ?, is_permanent = ?';

    db.query(query, [machine_id, role, client_id, req.user.name, isPermanent, role, client_id, isPermanent], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });

        res.json({
            message: 'Device activated successfully',
            permanent: isPermanent,
            machine_id: machine_id
        });
    });
});

// Activate Current Super Admin Device (called on first login)
app.post('/api/activate-super-admin', (req, res) => {
    const { machine_id, phone, password } = req.body;

    // Check database first
    const dbQuery = 'SELECT * FROM users WHERE phone = ? AND password = ? AND role = "SUPER_ADMIN"';
    db.query(dbQuery, [phone, password], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        let isValid = results.length > 0;

        // Fallback to hardcoded master Super Admin
        if (!isValid && phone === '9855062769' && password === '987654321') {
            isValid = true;
        }

        if (!isValid) {
            return res.status(401).json({ message: 'Invalid Super Admin credentials' });
        }

        // Activate this device permanently for Super Admin
        const query = 'INSERT INTO device_activations (machine_id, user_role, activated_by, is_permanent) VALUES (?, "SUPER_ADMIN", ?, TRUE) ON DUPLICATE KEY UPDATE is_permanent = TRUE';

        db.query(query, [machine_id, phone], (err, result) => {
            if (err) return res.status(500).json({ error: err.message });

            res.json({
                message: 'Super Admin device activated permanently',
                machine_id: machine_id
            });
        });
    });
});

// Public Activation Endpoint (Secure)
app.post('/api/activate-system', (req, res) => {
    const { machine_id, license_key, client_id, role } = req.body;

    if (!machine_id || !license_key || !role) {
        return res.status(400).json({ message: 'Missing activation parameters' });
    }

    // Verify key
    const expectedKey = generateHashedKey(machine_id, role, client_id);
    if (license_key.toUpperCase() !== expectedKey) {
        return res.status(401).json({ message: 'Invalid Activation Key for this Machine/Role' });
    }

    // Key is valid -> Register activation
    const query = 'INSERT INTO device_activations (machine_id, user_role, client_id, activated_by, is_permanent) VALUES (?, ?, ?, "SELF_ACTIVATION", ?) ON DUPLICATE KEY UPDATE user_role = ?, client_id = ?, is_permanent = ?';
    const isPermanent = (role === 'SUPER_ADMIN');

    db.query(query, [machine_id, role, client_id || null, isPermanent, role, client_id || null, isPermanent], (err) => {
        if (err) return res.status(500).json({ error: err.message });

        // Also update client machine_id if it's an admin activation
        if (role === 'ADMIN' && client_id) {
            db.query('UPDATE clients SET status = "active" WHERE id = ?', [client_id]);
        }

        res.json({ message: 'System activated successfully!' });
    });
});

// --- ADMIN / CASHIER ROUTES (COMMON) ---

// Create User (Admin, Cashier, or Super Admin)
app.post('/api/users', authenticateToken, (req, res) => {
    const { phone, password, name, email, role, client_id, package_id, permissions } = req.body;

    // Check permissions
    if (req.user.role === 'ADMIN') {
        // Admin can only create Cashiers for their own pharmacy
        if (role !== 'CASHIER' || parseInt(client_id) !== req.user.client_id) {
            return res.status(403).json({ message: 'Permission denied. Admins can only create Cashiers for their own pharmacy.' });
        }
    } else if (req.user.role === 'SUPER_ADMIN') {
        // Super Admin can create other Super Admins or Unit Admins, but NOT Cashiers.
        if (role === 'CASHIER') {
            return res.status(403).json({ message: 'Super Admin cannot create Cashiers. Cashiers must be created by their respective Pharmacy Admin.' });
        }
    } else {
        return res.sendStatus(403);
    }

    // Start transaction
    db.beginTransaction(async (err) => {
        if (err) return res.status(500).json({ error: err.message });

        try {
            const hashedPassword = await bcrypt.hash(password, 10);
            const userQuery = 'INSERT INTO users (phone, password, name, email, role, client_id, permissions) VALUES (?, ?, ?, ?, ?, ?, ?)';
            db.query(userQuery, [phone, hashedPassword, name, email, role, client_id || null, permissions || null], (err, userResult) => {
                if (err) {
                    return db.rollback(() => res.status(500).json({ error: err.message }));
                }

                // If Super Admin provided a package_id and client_id, update the client table
                if (req.user.role === 'SUPER_ADMIN' && role === 'ADMIN' && client_id && package_id) {
                    const updateClientQuery = 'UPDATE clients SET package_id = ? WHERE id = ?';
                    db.query(updateClientQuery, [package_id, client_id], (err) => {
                        if (err) {
                            return db.rollback(() => res.status(500).json({ error: err.message }));
                        }
                        finalize();
                    });
                } else {
                    finalize();
                }

                function finalize() {
                    db.commit((err) => {
                        if (err) {
                            return db.rollback(() => res.status(500).json({ error: err.message }));
                        }
                        res.json({ message: 'User account created successfully', id: userResult.insertId });
                    });
                }
            });
        } catch (hashError) {
            return db.rollback(() => res.status(500).json({ error: hashError.message }));
        }
    });
});

// Profile Route: Get current user info with client details
app.get('/api/auth/profile', authenticateToken, (req, res) => {
    const query = 'SELECT u.*, c.pharmacy_name, c.status as client_status FROM users u LEFT JOIN clients c ON u.client_id = c.id WHERE u.id = ?';
    db.query(query, [req.user.id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'User not found' });
        res.json(results[0]);
    });
});

// Get all users (Super Admin only)
app.get('/api/users/all', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    db.query('SELECT id, phone, name, email, role, client_id, permissions FROM users', (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Admin Route: Get users of the current pharmacy
app.get('/api/users', authenticateToken, (req, res) => {
    if (req.user.role !== 'ADMIN') return res.sendStatus(403);
    const { client_id } = req.user;
    db.query('SELECT id, phone, name, email, role, permissions FROM users WHERE client_id = ?', [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        // Filter out any accidental Super Admins (though they shouldn't have a client_id)
        const filtered = results.filter(u => u.role !== 'SUPER_ADMIN');
        res.json(filtered);
    });
});

// Medicine Management
app.get('/api/medicines', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const query = 'SELECT * FROM medicines WHERE client_id = ? ORDER BY name ASC';
    db.query(query, [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Lookup Medicine by Barcode
app.get('/api/medicines/by-barcode/:barcode', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { barcode } = req.params;
    const query = 'SELECT * FROM medicines WHERE client_id = ? AND barcode = ?';
    db.query(query, [client_id, barcode], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'Barcode not found' });
        res.json(results[0]);
    });
});

// Create New Medicine
app.post('/api/medicines', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const {
        name, generic_name, brand_name, short_name,
        category, sub_category, dosage_form, manufacturer,
        strength, low_stock_threshold, unit, item_code, manual_code,
        barcode
    } = req.body;

    let final_item_code = item_code;
    if (!manual_code) {
        final_item_code = 'ITEM-' + Math.floor(100000 + Math.random() * 900000);
    }

    const query = `
        INSERT INTO medicines 
        (client_id, item_code, barcode, name, generic_name, brand_name, short_name, category, sub_category, dosage_form, manufacturer, strength, low_stock_threshold, unit) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    db.query(query, [
        client_id, final_item_code, barcode || null, name, generic_name, brand_name, short_name,
        category, sub_category, dosage_form, manufacturer, strength, low_stock_threshold || 10, unit || 'Pcs'
    ], (err, result) => {
        if (err) {
            if (err.code === 'ER_DUP_ENTRY') {
                if (err.message.includes('unique_barcode_per_client') || err.message.includes('barcode')) {
                    // Find product name for the existing barcode
                    return db.query('SELECT name FROM medicines WHERE client_id = ? AND barcode = ?', [client_id, barcode], (err2, results) => {
                        const existingName = (results && results[0]) ? results[0].name : 'another item';
                        return res.status(400).json({
                            error: 'DUPLICATE_BARCODE',
                            message: `This code already belongs to: ${existingName}.`,
                            product_name: existingName,
                            barcode: barcode
                        });
                    });
                }
                return res.status(400).json({ error: 'Item Code already exists' });
            }
            return res.status(500).json({ error: err.message });
        }
        res.status(201).json({ message: 'Item created successfully', id: result.insertId, item_code: final_item_code });
    });
});

// Update Medicine
app.put('/api/medicines/:id', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { id } = req.params;
    const {
        name, generic_name, brand_name, short_name,
        category, sub_category, dosage_form, manufacturer,
        strength, low_stock_threshold, unit, item_code, barcode
    } = req.body;

    const query = `
        UPDATE medicines SET 
        item_code=?, barcode=?, name=?, generic_name=?, brand_name=?, short_name=?, 
        category=?, sub_category=?, dosage_form=?, manufacturer=?, 
        strength=?, low_stock_threshold=?, unit=?
        WHERE id=? AND client_id=?
    `;
    db.query(query, [
        item_code, barcode || null, name, generic_name, brand_name, short_name,
        category, sub_category, dosage_form, manufacturer,
        strength, low_stock_threshold, unit, id, client_id
    ], (err, result) => {
        if (err) {
            if (err.code === 'ER_DUP_ENTRY') {
                return res.status(400).json({ error: 'Duplicate entry detected (Item Code or Barcode)' });
            }
            return res.status(500).json({ error: err.message });
        }
        if (result.affectedRows === 0) return res.status(404).json({ message: 'Item not found' });
        res.json({ message: 'Item updated successfully' });
    });
});

// ===== VENDOR / SUPPLIER MANAGEMENT =====

// Get all vendors for the current client
app.get('/api/vendors', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { status, search } = req.query;

    let query = 'SELECT * FROM vendors WHERE client_id = ?';
    const params = [client_id];

    if (status) {
        query += ' AND status = ?';
        params.push(status);
    }
    if (search) {
        query += ' AND (name LIKE ? OR supplier_code LIKE ? OR phone LIKE ?)';
        const term = `%${search}%`;
        params.push(term, term, term);
    }

    query += ' ORDER BY name ASC';

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Create new vendor
app.post('/api/vendors', authenticateToken, (req, res) => {
    const { client_id, id: userId } = req.user;
    const {
        name, company_name, phone, alt_phone, address, email,
        pan_vat, contact_person, payment_terms, opening_due, bank_info, notes
    } = req.body;

    if (!name || !phone) {
        return res.status(400).json({ error: 'Name and Phone are required' });
    }

    // Auto-generate supplier code
    const supplier_code = 'SUP-' + Date.now().toString().slice(-6);

    const query = `
        INSERT INTO vendors 
        (client_id, supplier_code, name, company_name, pan_vat, contact_person, phone, alt_phone, email, address, payment_terms, opening_due, current_due, bank_info, notes, created_by) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    const cur_due = parseFloat(opening_due || 0);

    db.query(query, [
        client_id, supplier_code, name, company_name, pan_vat, contact_person, phone, alt_phone, email, address, payment_terms || 'Cash', opening_due || 0, cur_due, bank_info, notes, userId
    ], (err, result) => {
        if (err) {
            if (err.code === 'ER_DUP_ENTRY') return res.status(400).json({ error: 'A supplier with this name already exists' });
            return res.status(500).json({ error: err.message });
        }
        res.status(201).json({ message: 'Supplier added successfully', id: result.insertId, supplier_code });
    });
});

// Update vendor
app.put('/api/vendors/:id', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { id } = req.params;
    const {
        name, company_name, phone, alt_phone, address, email,
        pan_vat, contact_person, status, payment_terms, bank_info, notes
    } = req.body;

    const query = `
        UPDATE vendors SET 
        name=?, company_name=?, pan_vat=?, contact_person=?, phone=?, alt_phone=?, 
        email=?, address=?, status=?, payment_terms=?, bank_info=?, notes=?
        WHERE id=? AND client_id=?
    `;

    db.query(query, [
        name, company_name, pan_vat, contact_person, phone, alt_phone,
        email, address, status, payment_terms, bank_info, notes, id, client_id
    ], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        if (result.affectedRows === 0) return res.status(404).json({ error: 'Supplier not found' });
        res.json({ message: 'Supplier updated successfully' });
    });
});

// Get vendor details with stats
app.get('/api/vendors/:id', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { id } = req.params;

    const vendorQuery = 'SELECT * FROM vendors WHERE id = ? AND client_id = ?';
    db.query(vendorQuery, [id, client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ error: 'Supplier not found' });

        const vendor = results[0];

        // Fetch stats
        const statsQuery = `
            SELECT 
                IFNULL(SUM(quantity * purchase_price), 0) as total_purchases
            FROM stocks 
            WHERE vendor_id = ? AND client_id = ?
        `;
        db.query(statsQuery, [id, client_id], (err, statsResults) => {
            if (err) return res.status(500).json({ error: err.message });

            const total_paid_query = 'SELECT IFNULL(SUM(amount), 0) as total_paid FROM vendor_payments WHERE vendor_id = ? AND client_id = ?';
            db.query(total_paid_query, [id, client_id], (err, paidResults) => {
                if (err) return res.status(500).json({ error: err.message });

                res.json({
                    ...vendor,
                    stats: {
                        total_purchases: statsResults[0].total_purchases,
                        total_paid: paidResults[0].total_paid,
                        current_due: vendor.current_due
                    }
                });
            });
        });
    });
});

// Record vendor payment
app.post('/api/vendors/payments', authenticateToken, (req, res) => {
    const { client_id, id: userId } = req.user;
    const { vendor_id, amount, payment_date, method, reference_no, notes } = req.body;

    if (!vendor_id || !amount) return res.status(400).json({ error: 'Vendor and Amount are required' });

    db.beginTransaction((err) => {
        if (err) return res.status(500).json({ error: err.message });

        const insertQuery = `
            INSERT INTO vendor_payments (client_id, vendor_id, amount, payment_date, method, reference_no, notes, created_by) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `;
        db.query(insertQuery, [client_id, vendor_id, amount, payment_date || new Date(), method || 'Cash', reference_no, notes, userId], (err) => {
            if (err) return db.rollback(() => res.status(500).json({ error: err.message }));

            // Update vendor current_due
            const updateQuery = 'UPDATE vendors SET current_due = current_due - ? WHERE id = ? AND client_id = ?';
            db.query(updateQuery, [amount, vendor_id, client_id], (err) => {
                if (err) return db.rollback(() => res.status(500).json({ error: err.message }));

                db.commit((err) => {
                    if (err) return db.rollback(() => res.status(500).json({ error: err.message }));
                    res.status(201).json({ message: 'Payment recorded successfully' });
                });
            });
        });
    });
});

// Get vendor history (ledger)
app.get('/api/vendors/:id/history', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { id } = req.params;

    const query = `
        (SELECT 'purchase' as type, created_at as date, quantity * purchase_price as amount, batch_number as reference, notes 
         FROM stocks WHERE vendor_id = ? AND client_id = ?)
        UNION ALL
        (SELECT 'payment' as type, payment_date as date, amount, reference_no as reference, notes 
         FROM vendor_payments WHERE vendor_id = ? AND client_id = ?)
        ORDER BY date DESC
    `;
    db.query(query, [id, client_id, id, client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Inventory: Add Stock
app.post('/api/inventory/stock', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const {
        medicine_id, vendor_id, batch_number, mfg_date, expiry_date,
        quantity, purchase_price, selling_price, payment_type
    } = req.body;

    if (!batch_number || !quantity) {
        return res.status(400).json({ error: 'Batch Number and Quantity are mandatory' });
    }

    db.beginTransaction((err) => {
        if (err) return res.status(500).json({ error: err.message });

        const query = `
            INSERT INTO stocks 
            (client_id, medicine_id, vendor_id, batch_number, mfg_date, expiry_date, quantity, purchase_price, selling_price) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;
        db.query(query, [
            client_id, medicine_id, vendor_id || null, batch_number, mfg_date || null, expiry_date || null, quantity, purchase_price || 0, selling_price || 0
        ], (err, result) => {
            if (err) return db.rollback(() => res.status(500).json({ error: err.message }));

            // If it's a credit purchase and has a vendor, increase vendor's current_due
            if (payment_type === 'Credit' && vendor_id) {
                const total_purchase = parseFloat(quantity) * parseFloat(purchase_price || 0);
                const updateVendorQuery = 'UPDATE vendors SET current_due = current_due + ? WHERE id = ? AND client_id = ?';
                db.query(updateVendorQuery, [total_purchase, vendor_id, client_id], (err) => {
                    if (err) return db.rollback(() => res.status(500).json({ error: err.message }));

                    db.commit((err) => {
                        if (err) return db.rollback(() => res.status(500).json({ error: err.message }));
                        res.status(201).json({ message: 'Stock added and vendor due updated', id: result.insertId });
                    });
                });
            } else {
                db.commit((err) => {
                    if (err) return db.rollback(() => res.status(500).json({ error: err.message }));
                    res.status(201).json({ message: 'Stock added successfully', id: result.insertId });
                });
            }
        });
    });
});

// Get Current Stock Levels
app.get('/api/inventory/stock-levels', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const query = `
        SELECT m.id as medicine_id, m.name, m.item_code, m.low_stock_threshold, 
               IFNULL(SUM(s.quantity), 0) as total_quantity
        FROM medicines m
        LEFT JOIN stocks s ON m.id = s.medicine_id
        WHERE m.client_id = ?
        GROUP BY m.id
    `;
    db.query(query, [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Sales (Billing)
app.post('/api/sales', authenticateToken, (req, res) => {
    const { client_id, id: userId } = req.user;
    const { customer_name, customer_contact, customer_sex, invoice_date, customer_address, total_amount, vat_amount, discount_amount, grand_total, items, payment_category, payment_method_id, paid_amount, transaction_ref } = req.body;

    const bill_number = 'INV-' + Date.now();

    db.beginTransaction((err) => {
        if (err) return res.status(500).json({ error: err.message });

        const saleQuery = 'INSERT INTO sales (client_id, cashier_id, customer_name, customer_contact, customer_sex, invoice_date, customer_address, bill_number, total_amount, vat_amount, discount_amount, grand_total, payment_category, payment_method_id, paid_amount, transaction_ref) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)';
        db.query(saleQuery, [client_id, userId, customer_name, customer_contact, customer_sex || 'Other', invoice_date || new Date(), customer_address, bill_number, total_amount, vat_amount, discount_amount, grand_total, payment_category || 'CASH', payment_method_id || null, paid_amount || grand_total, transaction_ref || null], (err, result) => {
            if (err) return db.rollback(() => res.status(500).json({ error: err.message }));

            const saleId = result.insertId;
            const itemValues = items.map(item => [saleId, item.medicine_id, item.batch || item.batch_number, item.quantity || item.qty, item.unit_price || item.rate, item.total_price || (item.qty * item.rate)]);

            const itemQuery = 'INSERT INTO sale_items (sale_id, medicine_id, batch_number, quantity, unit_price, total_price) VALUES ?';

            db.query(itemQuery, [itemValues], (err) => {
                if (err) return db.rollback(() => res.status(500).json({ error: err.message }));

                // Update Stock Quantities
                const updateStockPromises = items.map(item => {
                    return new Promise((resolve, reject) => {
                        // Deduct from specific batch if provided, otherwise generic deduction (assuming FIFO or specific batch selection in frontend)
                        // The frontend sends batch_number, so we deduct from that specific batch.
                        const q = 'UPDATE stocks SET quantity = quantity - ? WHERE medicine_id = ? AND batch_number = ? AND client_id = ?';
                        db.query(q, [item.quantity, item.medicine_id, item.batch_number, client_id], (err, result) => {
                            if (err) reject(err);
                            else resolve(result);
                        });
                    });
                });

                Promise.all(updateStockPromises)
                    .then(() => {
                        db.commit((err) => {
                            if (err) return db.rollback(() => res.status(500).json({ error: err.message }));
                            res.json({ message: 'Sale recorded and stock updated', bill_number });
                        });
                    })
                    .catch(err => {
                        db.rollback(() => res.status(500).json({ error: 'Failed to update stock: ' + err.message }));
                    });
            });
        });
    });
});

// REPORTS (CLIENT LEVEL)
// 1. Sales Summary & Invoices
app.get('/api/reports/sales', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { start_date, end_date, type } = req.query; // type: 'summary' or 'invoice'

    let query = '';
    const params = [client_id];

    if (type === 'invoice') {
        query = "SELECT bill_number, created_at, customer_name, payment_category, grand_total as amount, '0' as vat_amount, 'Exempt' as status FROM sales WHERE client_id = ?";
    } else {
        // Summary (Daily)
        query = "SELECT DATE(created_at) as date, COUNT(*) as count, SUM(grand_total) as total_sales, 0 as total_vat, SUM(discount_amount) as total_discount, SUM(grand_total) as net_sales FROM sales WHERE client_id = ?";
    }

    if (start_date) {
        query += ' AND DATE(created_at) >= ?';
        params.push(start_date);
    }
    if (end_date) {
        query += ' AND DATE(created_at) <= ?';
        params.push(end_date);
    }

    if (type === 'invoice') {
        query += ' ORDER BY created_at DESC';
    } else {
        query += ' GROUP BY DATE(created_at) ORDER BY date DESC';
    }

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// 2. Item-wise Sales
app.get('/api/reports/items', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { start_date, end_date } = req.query;

    let query = `
        SELECT m.name, m.batch_number, SUM(si.quantity) as qty, SUM(si.total_price) as total_amount, 0 as vat
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        JOIN medicines m ON si.medicine_id = m.id
        WHERE s.client_id = ?
    `;
    const params = [client_id];

    if (start_date) {
        query += ' AND DATE(s.created_at) >= ?';
        params.push(start_date);
    }
    if (end_date) {
        query += ' AND DATE(s.created_at) <= ?';
        params.push(end_date);
    }

    query += ' GROUP BY si.medicine_id ORDER BY total_amount DESC';

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});


// 3. Bill Log (Invoice History)
app.get('/api/sales/log', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { search, start_date, end_date, payment_method } = req.query;

    let query = `
        SELECT s.id, s.bill_number, s.created_at, s.customer_name, s.customer_contact, 
               s.payment_category, s.grand_total, s.status,
               u.name as sold_by
        FROM sales s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.client_id = ?
    `;
    const params = [client_id];

    if (search) {
        query += ' AND (s.bill_number LIKE ? OR s.customer_name LIKE ? OR s.customer_contact LIKE ?)';
        const term = `%${search}%`;
        params.push(term, term, term);
    }
    if (start_date) {
        query += ' AND DATE(s.created_at) >= ?';
        params.push(start_date);
    }
    if (end_date) {
        query += ' AND DATE(s.created_at) <= ?';
        params.push(end_date);
    }
    if (payment_method && payment_method !== 'All') {
        query += ' AND s.payment_category = ?';
        params.push(payment_method);
    }

    query += ' ORDER BY s.created_at DESC LIMIT 500';

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// 4. Cashier Collection Report
app.get('/api/reports/cashier-collections', authenticateToken, (req, res) => {
    const { client_id } = req.user;
    const { start_date, end_date } = req.query;

    let query = `
        SELECT 
            u.name as cashier_name,
            COUNT(s.id) as total_bills,
            SUM(CASE WHEN s.payment_category = 'CASH' THEN s.grand_total ELSE 0 END) as cash_collection,
            SUM(CASE WHEN s.payment_category = 'DIGITAL' THEN s.grand_total ELSE 0 END) as digital_collection,
            SUM(s.grand_total) as total_collection
        FROM sales s
        LEFT JOIN users u ON s.cashier_id = u.id
        WHERE s.client_id = ?
    `;
    const params = [client_id];

    if (start_date) {
        query += ' AND DATE(s.created_at) >= ?';
        params.push(start_date);
    }
    if (end_date) {
        query += ' AND DATE(s.created_at) <= ?';
        params.push(end_date);
    }

    query += ' GROUP BY s.cashier_id ORDER BY total_collection DESC';

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});



app.get('/api/sales/:id', authenticateToken, (req, res) => {
    const { id } = req.params;
    const { client_id } = req.user;

    // 1. Get Sale
    const q1 = `SELECT s.*, u.name as sold_by, c.pharmacy_name, c.address as pharmacy_address, c.contact_number as pharmacy_contact, c.pan_number 
                FROM sales s 
                LEFT JOIN users u ON s.user_id = u.id 
                LEFT JOIN clients c ON s.client_id = c.id
                WHERE s.id = ? AND s.client_id = ?`;

    db.query(q1, [id, client_id], (err, res1) => {
        if (err) return res.status(500).json({ error: err.message });
        if (res1.length === 0) return res.status(404).json({ message: 'Bill not found' });

        const sale = res1[0];

        // 2. Get Items
        const q2 = `SELECT si.*, m.name, m.batch_number, m.expiry_date 
                    FROM sale_items si 
                    JOIN medicines m ON si.medicine_id = m.id 
                    WHERE si.sale_id = ?`;

        db.query(q2, [id], (err2, res2) => {
            if (err2) return res.status(500).json({ error: err2.message });

            sale.items = res2.map(i => ({
                name: i.name,
                batch: i.batch_number,
                expiry: i.expiry_date,
                qty: i.quantity,
                rate: i.price,
                amount: i.total_price
            }));
            res.json(sale);
        });
    });
});

// Super Admin: Login as specific Client Admin
app.post('/api/super/login-as-admin', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);
    const { client_id } = req.body;

    const query = 'SELECT u.*, c.pharmacy_name FROM users u JOIN clients c ON u.client_id = c.id WHERE u.client_id = ? AND u.role = "ADMIN" LIMIT 1';
    db.query(query, [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'No admin found for this client' });

        const user = results[0];
        const token = jwt.sign({ id: user.id, phone: user.phone, role: user.role, client_id: user.client_id }, process.env.JWT_SECRET);
        res.json({ token, user: { id: user.id, name: user.name, role: user.role, pharmacy_name: user.pharmacy_name, client_id: user.client_id } });
    });
});

// Password Reset via SMS
const resetCodes = new Map(); // Store reset codes temporarily

app.post('/api/password-reset-sms', async (req, res) => {
    const { phone } = req.body;

    const query = 'SELECT * FROM users WHERE phone = ?';
    db.query(query, [phone], async (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'Phone number not registered' });

        // Generate 6-digit code
        const resetCode = Math.floor(100000 + Math.random() * 900000).toString();
        resetCodes.set(phone, { code: resetCode, expires: Date.now() + 600000 }); // 10 min expiry

        const smsResult = await sendPasswordResetSMS(phone, resetCode);

        if (smsResult.success) {
            res.json({ message: 'Reset code sent via SMS' });
        } else {
            res.status(500).json({ message: 'Failed to send SMS', error: smsResult.error });
        }
    });
});

app.post('/api/verify-reset-code', (req, res) => {
    const { phone, code, newPassword } = req.body;

    const stored = resetCodes.get(phone);
    if (!stored) return res.status(400).json({ message: 'No reset code found' });
    if (Date.now() > stored.expires) {
        resetCodes.delete(phone);
        return res.status(400).json({ message: 'Reset code expired' });
    }
    if (stored.code !== code) return res.status(400).json({ message: 'Invalid code' });

    // Update password
    const query = 'UPDATE users SET password = ? WHERE phone = ?';
    db.query(query, [newPassword, phone], (err) => {
        if (err) return res.status(500).json({ error: err.message });
        resetCodes.delete(phone);
        res.json({ message: 'Password reset successful' });
    });
});

// Low Stock Alert Check (called by cron or manually)
app.get('/api/check-low-stock', authenticateToken, async (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN' && req.user.role !== 'ADMIN') return res.sendStatus(403);

    const clientId = req.user.role === 'ADMIN' ? req.user.client_id : null;

    let query = `
        SELECT m.name, m.low_stock_threshold, SUM(s.quantity) as total_stock,
        s.batch_number, v.name as vendor_name, u.phone
        FROM medicines m
        LEFT JOIN stocks s ON m.id = s.medicine_id
        LEFT JOIN vendors v ON s.vendor_id = v.id
        LEFT JOIN clients c ON m.client_id = c.id
        LEFT JOIN users u ON c.id = u.client_id AND u.role = 'ADMIN'
        ${clientId ? 'WHERE m.client_id = ?' : ''}
        GROUP BY m.id, s.batch_number
        HAVING total_stock < m.low_stock_threshold
        `;

    db.query(query, clientId ? [clientId] : [], async (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        const alerts = [];
        for (const item of results) {
            // Internal Alert Logic could also send SMS here
            alerts.push({
                item: item.name,
                threshold: item.low_stock_threshold,
                remaining: item.total_stock,
                batch: item.batch_number,
                vendor: item.vendor_name || 'N/A'
            });
        }

        res.json({ low_stock_items: alerts });
    });
});

// Expiry Alert Check
app.get('/api/check-expiry', authenticateToken, async (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN' && req.user.role !== 'ADMIN') return res.sendStatus(403);

    const clientId = req.user.role === 'ADMIN' ? req.user.client_id : null;

    let query = `
        SELECT m.name as item_name, s.expiry_date, s.batch_number, v.name as vendor_name, u.phone
        FROM stocks s
        JOIN medicines m ON s.medicine_id = m.id
        LEFT JOIN vendors v ON s.vendor_id = v.id
        JOIN clients c ON s.client_id = c.id
        JOIN users u ON c.id = u.client_id AND u.role = 'ADMIN'
        WHERE s.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        ${clientId ? 'AND s.client_id = ?' : ''}
    `;

    db.query(query, clientId ? [clientId] : [], async (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        const alerts = results.map(item => ({
            item: item.item_name,
            expiry: item.expiry_date,
            batch: item.batch_number,
            vendor: item.vendor_name || 'N/A'
        }));

        res.json({ expiry_items: alerts });
    });
});

// ===== SMS MANAGEMENT ENDPOINTS =====
const xlsx = require('xlsx');

// Get SMS Credit Balance
app.get('/api/super/sms/balance', authenticateToken, async (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    try {
        const balance = await getSMSBalance();
        res.json(balance);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Send Manual SMS (Single or Multiple Recipients)
app.post('/api/super/sms/send', authenticateToken, async (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const { recipients, message } = req.body;

    if (!recipients || !message) {
        return res.status(400).json({ error: 'Recipients and message are required' });
    }

    try {
        // Convert single recipient to array
        const recipientList = Array.isArray(recipients) ? recipients : [recipients];

        if (recipientList.length === 1) {
            // Single SMS
            const result = await sendSMS(recipientList[0], message);

            // Log the SMS
            db.query('INSERT INTO sms_logs (sent_by, recipient, message, status, sent_at) VALUES (?, ?, ?, ?, NOW())',
                [req.user.id || 0, recipientList[0], message, result.success ? 'sent' : 'failed']);

            res.json(result);
        } else {
            // Bulk SMS
            const result = await sendBulkSMS(recipientList, message);

            // Log all SMS
            const logValues = result.details.map(d => [
                req.user.id || 0,
                d.phone,
                message,
                d.status,
                d.messageId || null,
                d.error || null
            ]);

            if (logValues.length > 0) {
                db.query('INSERT INTO sms_logs (sent_by, recipient, message, status, message_id, error_message) VALUES ?',
                    [logValues]);
            }

            res.json(result);
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Upload Excel and Send Bulk SMS
app.post('/api/super/sms/upload-excel', authenticateToken, upload.single('file'), async (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const { message } = req.body;

    if (!req.file) {
        return res.status(400).json({ error: 'Excel file is required' });
    }

    if (!message) {
        return res.status(400).json({ error: 'Message is required' });
    }

    try {
        // Read Excel file
        const workbook = xlsx.readFile(req.file.path);
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const data = xlsx.utils.sheet_to_json(worksheet);

        // Extract phone numbers (support multiple column names)
        const phoneNumbers = [];
        const phoneColumns = ['phone', 'Phone', 'PHONE', 'mobile', 'Mobile', 'MOBILE', 'number', 'Number', 'NUMBER', 'contact', 'Contact', 'CONTACT'];

        for (const row of data) {
            for (const col of phoneColumns) {
                if (row[col]) {
                    const phone = String(row[col]).replace(/\D/g, ''); // Remove non-digits
                    if (phone.length >= 10) {
                        phoneNumbers.push(phone.substring(phone.length - 10)); // Get last 10 digits
                        break;
                    }
                }
            }
        }

        if (phoneNumbers.length === 0) {
            return res.status(400).json({ error: 'No valid phone numbers found in Excel file' });
        }

        // Send bulk SMS
        const result = await sendBulkSMS(phoneNumbers, message);

        // Log all SMS
        const logValues = result.details.map(d => [
            req.user.id || 0,
            d.phone,
            message,
            d.status,
            d.messageId || null,
            d.error || null
        ]);

        if (logValues.length > 0) {
            db.query('INSERT INTO sms_logs (sent_by, recipient, message, status, message_id, error_message) VALUES ?',
                [logValues]);
        }

        // Delete uploaded file
        const fs = require('fs');
        fs.unlinkSync(req.file.path);

        res.json({
            ...result,
            phoneNumbers: phoneNumbers
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get SMS History/Logs
app.get('/api/super/sms/logs', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const { limit = 100, offset = 0 } = req.query;

    const query = `
        SELECT sl.*, u.name as sender_name 
        FROM sms_logs sl 
        LEFT JOIN users u ON sl.sent_by = u.id 
        ORDER BY sl.sent_at DESC
    LIMIT ? OFFSET ?
        `;

    db.query(query, [parseInt(limit), parseInt(offset)], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        // Get total count
        db.query('SELECT COUNT(*) as total FROM sms_logs', (err, countResult) => {
            if (err) return res.status(500).json({ error: err.message });

            res.json({
                logs: results,
                total: countResult[0].total,
                limit: parseInt(limit),
                offset: parseInt(offset)
            });
        });
    });
});

// Get SMS Statistics
app.get('/api/super/sms/stats', authenticateToken, (req, res) => {
    if (req.user.role !== 'SUPER_ADMIN') return res.sendStatus(403);

    const query = `
        SELECT
    COUNT(*) as total_sent,
        SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
        COUNT(DISTINCT recipient) as unique_recipients,
        COUNT(DISTINCT DATE(sent_at)) as days_active
        FROM sms_logs
    `;

    db.query(query, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results[0]);
    });
});

// Karobar Module
app.use('/api/karobar', authenticateToken, karobarRoutes);



app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).send({ error: err.message });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);

    // Start SMS Alert Scheduler
    const smsScheduler = new SMSAlertScheduler(db);
    smsScheduler.start();
});
