const express = require('express');
const router = express.Router();
const multer = require('multer');
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 2 * 1024 * 1024 } // 2MB limit
});

// Middleware to ensure user is ADMIN
const requireAdmin = (req, res, next) => {
    if (req.user && req.user.role === 'ADMIN') {
        next();
    } else {
        res.status(403).json({ message: 'Access denied: Admin only' });
    }
};

// GET /api/bill-design
router.get('/bill-design', requireAdmin, (req, res) => {
    const clientId = req.user.client_id;
    if (!clientId) return res.status(400).json({ message: 'Client ID missing' });

    const sql = `SELECT id, paper_size, orientation, config, 
                 TO_BASE64(stamp_image) as stamp_base64, 
                 TO_BASE64(signature_image) as signature_base64 
                 FROM bill_designs WHERE client_id = ?`;

    req.app.get('db').query(sql, [clientId], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) {
            return res.json({ found: false }); // Frontend will use defaults
        }
        res.json({ found: true, design: results[0] });
    });
});

// POST /api/bill-design
// Handles JSON config + Optional Images
const validUpload = upload.fields([
    { name: 'stamp_image', maxCount: 1 },
    { name: 'signature_image', maxCount: 1 }
]);

router.post('/bill-design', requireAdmin, validUpload, (req, res) => {
    const clientId = req.user.client_id;
    const { paper_size, orientation, config } = req.body;

    if (!clientId) return res.status(400).json({ message: 'Client ID missing' });

    // Prepare query
    let stampBuffer = null;
    let signatureBuffer = null;

    if (req.files && req.files['stamp_image']) stampBuffer = req.files['stamp_image'][0].buffer;
    if (req.files && req.files['signature_image']) signatureBuffer = req.files['signature_image'][0].buffer;

    // Check if exists
    const checkSql = "SELECT id FROM bill_designs WHERE client_id = ?";
    req.app.get('db').query(checkSql, [clientId], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        if (results.length > 0) {
            // Update
            let updateSql = "UPDATE bill_designs SET paper_size=?, orientation=?, config=?, updated_at=NOW()";
            const params = [paper_size, orientation, config];

            if (stampBuffer) {
                updateSql += ", stamp_image=?";
                params.push(stampBuffer);
            }
            if (signatureBuffer) {
                updateSql += ", signature_image=?";
                params.push(signatureBuffer);
            }

            updateSql += " WHERE client_id=?";
            params.push(clientId);

            req.app.get('db').query(updateSql, params, (err) => {
                if (err) return res.status(500).json({ error: err.message });
                res.json({ message: 'Design updated successfully' });
            });
        } else {
            // Insert
            const insertSql = `INSERT INTO bill_designs 
                (client_id, paper_size, orientation, config, stamp_image, signature_image) 
                VALUES (?, ?, ?, ?, ?, ?)`;
            req.app.get('db').query(insertSql,
                [clientId, paper_size, orientation, config, stampBuffer, signatureBuffer],
                (err) => {
                    if (err) return res.status(500).json({ error: err.message });
                    res.json({ message: 'Design saved successfully' });
                });
        }
    });
});

module.exports = router;
