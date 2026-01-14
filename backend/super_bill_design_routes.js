const express = require('express');
const router = express.Router();

// Middleware to ensure user is SUPER_ADMIN
const requireSuperAdmin = (req, res, next) => {
    if (req.user && req.user.role === 'SUPER_ADMIN') {
        next();
    } else {
        res.status(403).json({ message: 'Access denied: Super Admin only' });
    }
};

// GET /api/super/bill-designs - Get all bill design templates
router.get('/super/bill-designs', requireSuperAdmin, (req, res) => {
    const sql = 'SELECT id, name, design_data, created_at, updated_at FROM super_bill_templates ORDER BY created_at DESC';

    req.app.get('db').query(sql, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// POST /api/super/bill-designs - Save a new design template
router.post('/super/bill-designs', requireSuperAdmin, (req, res) => {
    const { name, design_data } = req.body;

    if (!name || !design_data) {
        return res.status(400).json({ message: 'Name and design_data are required' });
    }

    const sql = 'INSERT INTO super_bill_templates (name, design_data) VALUES (?, ?)';

    req.app.get('db').query(sql, [name, design_data], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Design saved successfully', id: result.insertId });
    });
});

// POST /api/super/bill-designs/publish - Publish design to specific clients
router.post('/super/bill-designs/publish', requireSuperAdmin, (req, res) => {
    const { design_id, client_ids } = req.body;

    if (!design_id) {
        return res.status(400).json({ message: 'design_id is required' });
    }

    // If client_ids is 'all', apply to all clients
    if (client_ids === 'all') {
        const sql = `
            INSERT INTO client_bill_designs (client_id, bill_design_id) 
            SELECT id, ? FROM clients 
            ON DUPLICATE KEY UPDATE bill_design_id = ?
        `;
        req.app.get('db').query(sql, [design_id, design_id], (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ message: 'Design published to all clients successfully' });
        });
    } else if (Array.isArray(client_ids) && client_ids.length > 0) {
        // Publish to specific clients
        const values = client_ids.map(cid => [cid, design_id]);
        const sql = `
            INSERT INTO client_bill_designs (client_id, bill_design_id) 
            VALUES ? 
            ON DUPLICATE KEY UPDATE bill_design_id = ?
        `;
        req.app.get('db').query(sql, [values, design_id], (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ message: 'Design published to selected clients successfully' });
        });
    } else {
        res.status(400).json({ message: 'Invalid client_ids format' });
    }
});

// DELETE /api/super/bill-designs/:id - Delete a design template
router.delete('/super/bill-designs/:id', requireSuperAdmin, (req, res) => {
    const { id } = req.params;

    const sql = 'DELETE FROM super_bill_templates WHERE id = ?';
    req.app.get('db').query(sql, [id], (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Design deleted successfully' });
    });
});

module.exports = router;
