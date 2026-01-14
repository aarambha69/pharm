const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Configure multer for QR image upload
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const clientId = req.user.client_id;
        const uploadPath = path.join(__dirname, 'uploads', 'payment_qr', clientId.toString());

        // Create directory if it doesn't exist
        if (!fs.existsSync(uploadPath)) {
            fs.mkdirSync(uploadPath, { recursive: true });
        }
        cb(null, uploadPath);
    },
    filename: (req, file, cb) => {
        const methodId = req.params.id || 'temp';
        const ext = path.extname(file.originalname);
        cb(null, `${methodId}${ext}`);
    }
});

const upload = multer({
    storage: storage,
    limits: { fileSize: 2 * 1024 * 1024 }, // 2MB limit
    fileFilter: (req, file, cb) => {
        const allowedTypes = /jpeg|jpg|png/;
        const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = allowedTypes.test(file.mimetype);

        if (extname && mimetype) {
            return cb(null, true);
        } else {
            cb(new Error('Only PNG and JPG images are allowed'));
        }
    }
});

// Helper to get DB connection
const getDb = (req) => req.app.get('db');

// GET /api/payment-methods - List all payment methods
router.get('/payment-methods', (req, res) => {
    const db = getDb(req);
    const { client_id } = req.user;
    const { category, status, show_on_billing } = req.query;

    let query = 'SELECT * FROM payment_methods WHERE client_id = ?';
    const params = [client_id];

    if (category) {
        query += ' AND category = ?';
        params.push(category);
    }

    if (status) {
        query += ' AND status = ?';
        params.push(status);
    }

    if (show_on_billing !== undefined) {
        query += ' AND show_on_billing = ?';
        params.push(show_on_billing === 'true' ? 1 : 0);
    }

    query += ' ORDER BY category, name';

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// GET /api/payment-methods/:id - Get single payment method
router.get('/payment-methods/:id', (req, res) => {
    const db = getDb(req);
    const { client_id } = req.user;

    db.query('SELECT * FROM payment_methods WHERE id = ? AND client_id = ?',
        [req.params.id, client_id], (err, results) => {
            if (err) return res.status(500).json({ error: err.message });
            if (results.length === 0) return res.status(404).json({ error: 'Payment method not found' });
            res.json(results[0]);
        });
});

// POST /api/payment-methods - Create new payment method
router.post('/payment-methods', (req, res) => {
    const db = getDb(req);
    const { client_id, role } = req.user;

    // Only Admin/Super Admin can create
    if (!['ADMIN', 'SUPER_ADMIN'].includes(role)) {
        return res.status(403).json({ error: 'Permission denied' });
    }

    const {
        name, category, provider, account_name, account_id,
        phone_number, notes, status, show_on_billing
    } = req.body;

    // Validations
    if (!name || !category) {
        return res.status(400).json({ error: 'Name and category are required' });
    }

    if (!['CASH', 'DIGITAL'].includes(category)) {
        return res.status(400).json({ error: 'Invalid category' });
    }

    // Check for duplicate name (case-insensitive)
    db.query('SELECT id FROM payment_methods WHERE client_id = ? AND LOWER(name) = LOWER(?) AND status = "Active"',
        [client_id, name], (err, existing) => {
            if (err) return res.status(500).json({ error: err.message });
            if (existing.length > 0) {
                return res.status(400).json({ error: 'Payment method with this name already exists' });
            }

            const query = `
            INSERT INTO payment_methods 
            (client_id, name, category, provider, account_name, account_id, phone_number, notes, status, show_on_billing)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;

            db.query(query, [
                client_id, name, category, provider || null, account_name || null,
                account_id || null, phone_number || null, notes || null,
                status || 'Active', show_on_billing !== false ? 1 : 0
            ], (err, result) => {
                if (err) return res.status(500).json({ error: err.message });
                res.status(201).json({
                    message: 'Payment method created successfully',
                    id: result.insertId
                });
            });
        });
});

// PUT /api/payment-methods/:id - Update payment method
router.put('/payment-methods/:id', (req, res) => {
    const db = getDb(req);
    const { client_id, role } = req.user;

    // Only Admin/Super Admin can update
    if (!['ADMIN', 'SUPER_ADMIN'].includes(role)) {
        return res.status(403).json({ error: 'Permission denied' });
    }

    const {
        name, category, provider, account_name, account_id,
        phone_number, notes, status, show_on_billing
    } = req.body;

    // Check if method exists and belongs to client
    db.query('SELECT id FROM payment_methods WHERE id = ? AND client_id = ?',
        [req.params.id, client_id], (err, existing) => {
            if (err) return res.status(500).json({ error: err.message });
            if (existing.length === 0) {
                return res.status(404).json({ error: 'Payment method not found' });
            }

            // Check for duplicate name (excluding current record)
            db.query('SELECT id FROM payment_methods WHERE client_id = ? AND LOWER(name) = LOWER(?) AND id != ? AND status = "Active"',
                [client_id, name, req.params.id], (err, duplicate) => {
                    if (err) return res.status(500).json({ error: err.message });
                    if (duplicate.length > 0) {
                        return res.status(400).json({ error: 'Payment method with this name already exists' });
                    }

                    const query = `
                UPDATE payment_methods 
                SET name = ?, category = ?, provider = ?, account_name = ?, account_id = ?,
                    phone_number = ?, notes = ?, status = ?, show_on_billing = ?
                WHERE id = ? AND client_id = ?
            `;

                    db.query(query, [
                        name, category, provider || null, account_name || null, account_id || null,
                        phone_number || null, notes || null, status || 'Active',
                        show_on_billing !== false ? 1 : 0, req.params.id, client_id
                    ], (err) => {
                        if (err) return res.status(500).json({ error: err.message });
                        res.json({ message: 'Payment method updated successfully' });
                    });
                });
        });
});

// DELETE /api/payment-methods/:id - Delete payment method
router.delete('/payment-methods/:id', (req, res) => {
    const db = getDb(req);
    const { client_id, role } = req.user;

    // Only Admin/Super Admin can delete
    if (!['ADMIN', 'SUPER_ADMIN'].includes(role)) {
        return res.status(403).json({ error: 'Permission denied' });
    }

    // Check if method is used in any sales
    db.query('SELECT COUNT(*) as count FROM sales WHERE payment_method_id = ?',
        [req.params.id], (err, results) => {
            if (err) return res.status(500).json({ error: err.message });

            if (results[0].count > 0) {
                // Soft delete - set to inactive
                db.query('UPDATE payment_methods SET status = "Inactive" WHERE id = ? AND client_id = ?',
                    [req.params.id, client_id], (err) => {
                        if (err) return res.status(500).json({ error: err.message });
                        res.json({ message: 'Payment method deactivated (used in transactions)' });
                    });
            } else {
                // Hard delete
                db.query('DELETE FROM payment_methods WHERE id = ? AND client_id = ?',
                    [req.params.id, client_id], (err) => {
                        if (err) return res.status(500).json({ error: err.message });

                        // Delete QR image file if exists
                        const qrPath = path.join(__dirname, 'uploads', 'payment_qr', client_id.toString(), `${req.params.id}.png`);
                        if (fs.existsSync(qrPath)) {
                            fs.unlinkSync(qrPath);
                        }

                        res.json({ message: 'Payment method deleted successfully' });
                    });
            }
        });
});

// POST /api/payment-methods/:id/upload-qr - Upload QR image as BLOB
router.post('/payment-methods/:id/upload-qr', upload.single('qr_image'), (req, res) => {
    const db = getDb(req);
    const { client_id, role } = req.user;

    // Only Admin/Super Admin can upload
    if (!['ADMIN', 'SUPER_ADMIN'].includes(role)) {
        return res.status(403).json({ error: 'Permission denied' });
    }

    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }

    // Read file as buffer for BLOB storage
    const qrBuffer = fs.readFileSync(req.file.path);

    // Update payment method with QR BLOB
    db.query('UPDATE payment_methods SET qr_image_blob = ? WHERE id = ? AND client_id = ?',
        [qrBuffer, req.params.id, client_id], (err) => {
            if (err) {
                // Delete uploaded file on error
                fs.unlinkSync(req.file.path);
                return res.status(500).json({ error: err.message });
            }

            // Delete temp file after successful BLOB storage
            fs.unlinkSync(req.file.path);

            res.json({
                message: 'QR image uploaded successfully',
                has_qr: true
            });
        });
});

// GET /api/payment-methods/:id/qr - Get QR image as base64
router.get('/payment-methods/:id/qr', (req, res) => {
    const db = getDb(req);
    const { client_id } = req.user;

    db.query('SELECT qr_image_blob FROM payment_methods WHERE id = ? AND client_id = ?',
        [req.params.id, client_id], (err, results) => {
            if (err) return res.status(500).json({ error: err.message });
            if (results.length === 0 || !results[0].qr_image_blob) {
                return res.status(404).json({ error: 'QR image not found' });
            }

            // Convert BLOB to base64
            const base64Image = results[0].qr_image_blob.toString('base64');
            res.json({ qr_image: `data:image/png;base64,${base64Image}` });
        });
});

module.exports = router;
