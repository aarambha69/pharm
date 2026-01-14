const express = require('express');
const router = express.Router();

// Middleware
const requireAuth = (req, res, next) => {
    if (req.user) next();
    else res.status(401).json({ message: 'Unauthorized' });
};

const requireAdmin = (req, res, next) => {
    if (req.user && (req.user.role === 'ADMIN' || req.user.role === 'SUPER_ADMIN')) next();
    else res.status(403).json({ message: 'Admin access required' });
};

// GET /api/notifications - Get active notifications for logged-in user (cashier/admin)
router.get('/notifications', requireAuth, (req, res) => {
    const user_id = req.user.id;
    const client_id = req.user.client_id;
    const today = new Date().toISOString().split('T')[0];

    const query = `
        SELECT DISTINCT n.*, nr.is_read, nr.read_at,
               u.name as created_by_name
        FROM notifications n
        JOIN notification_recipients nr ON n.id = nr.notification_id
        LEFT JOIN users u ON n.created_by = u.id
        WHERE n.client_id = ?
        AND n.is_active = TRUE
        AND ? BETWEEN n.start_date AND n.end_date
        AND (nr.user_id = ? OR nr.is_all_cashiers = TRUE)
        ORDER BY n.priority DESC, n.created_at DESC
    `;

    req.app.get('db').query(query, [client_id, today, user_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// GET /api/notifications/admin - Admin view all notifications
router.get('/notifications/admin', requireAdmin, (req, res) => {
    const client_id = req.user.client_id;
    const { status } = req.query; // 'active', 'expired', 'upcoming'
    const today = new Date().toISOString().split('T')[0];

    let query = `
        SELECT n.*, u.name as created_by_name,
               COUNT(DISTINCT nr.id) as total_recipients,
               COUNT(DISTINCT CASE WHEN nr.is_read = TRUE THEN nr.id END) as read_count
        FROM notifications n
        LEFT JOIN users u ON n.created_by = u.id
        LEFT JOIN notification_recipients nr ON n.id = nr.notification_id
        WHERE n.client_id = ?
    `;

    const params = [client_id];

    if (status === 'active') {
        query += ` AND ? BETWEEN n.start_date AND n.end_date`;
        params.push(today);
    } else if (status === 'expired') {
        query += ` AND n.end_date < ?`;
        params.push(today);
    } else if (status === 'upcoming') {
        query += ` AND n.start_date > ?`;
        params.push(today);
    }

    query += ` GROUP BY n.id ORDER BY n.created_at DESC`;

    req.app.get('db').query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// POST /api/notifications - Create notification (admin only)
router.post('/notifications', requireAdmin, (req, res) => {
    const { title, description, priority, start_date, end_date, target, cashier_ids } = req.body;
    const client_id = req.user.client_id;
    const created_by = req.user.id;

    // Validation
    if (!title || !description || !start_date || !end_date) {
        return res.status(400).json({ message: 'Title, description, start date, and end date are required' });
    }

    if (new Date(end_date) < new Date(start_date)) {
        return res.status(400).json({ message: 'End date must be greater than or equal to start date' });
    }

    if (target !== 'all' && (!cashier_ids || cashier_ids.length === 0)) {
        return res.status(400).json({ message: 'Please select at least one cashier' });
    }

    // Insert notification
    const notifQuery = `
        INSERT INTO notifications (client_id, title, description, priority, start_date, end_date, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    `;

    req.app.get('db').query(notifQuery, [
        client_id, title, description, priority || 'normal', start_date, end_date, created_by
    ], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });

        const notification_id = result.insertId;

        // Insert recipients
        if (target === 'all') {
            // Target all cashiers
            const recipientQuery = `INSERT INTO notification_recipients (notification_id, is_all_cashiers) VALUES (?, TRUE)`;
            req.app.get('db').query(recipientQuery, [notification_id], (err) => {
                if (err) return res.status(500).json({ error: err.message });
                res.json({ message: 'Notification created successfully', id: notification_id });
            });
        } else {
            // Target specific cashiers
            const values = cashier_ids.map(id => [notification_id, id, false]);
            const recipientQuery = `INSERT INTO notification_recipients (notification_id, user_id, is_all_cashiers) VALUES ?`;
            req.app.get('db').query(recipientQuery, [values], (err) => {
                if (err) return res.status(500).json({ error: err.message });
                res.json({ message: 'Notification created successfully', id: notification_id });
            });
        }
    });
});

// POST /api/notifications/:id/read - Mark notification as read
router.post('/notifications/:id/read', requireAuth, (req, res) => {
    const notification_id = req.params.id;
    const user_id = req.user.id;

    const query = `
        UPDATE notification_recipients 
        SET is_read = TRUE, read_at = NOW()
        WHERE notification_id = ? AND (user_id = ? OR is_all_cashiers = TRUE)
    `;

    req.app.get('db').query(query, [notification_id, user_id], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Notification marked as read' });
    });
});

// GET /api/users/cashiers - Get list of cashiers for targeting
router.get('/users/cashiers', requireAdmin, (req, res) => {
    const client_id = req.user.client_id;

    const query = `
        SELECT id, name, phone 
        FROM users 
        WHERE client_id = ? AND role = 'CASHIER' AND status = 'active'
        ORDER BY name ASC
    `;

    req.app.get('db').query(query, [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

module.exports = router;
