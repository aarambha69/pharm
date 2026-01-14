const express = require('express');
const router = express.Router();
const {
    sendLowStockAlertEnhanced,
    sendExpiryAlertEnhanced,
    sendDailySummarySMS,
    logSMS,
    getSMSBalance
} = require('./services/sms');

// Middleware to ensure user is ADMIN
const requireAdmin = (req, res, next) => {
    if (req.user && (req.user.role === 'ADMIN' || req.user.role === 'SUPER_ADMIN')) {
        next();
    } else {
        res.status(403).json({ message: 'Access denied: Admin only' });
    }
};

// POST /api/sms/send-alert - Send individual SMS alert
router.post('/sms/send-alert', requireAdmin, async (req, res) => {
    const { type, productData, toNumber } = req.body;
    const client_id = req.user.client_id;

    if (!type || !productData || !toNumber) {
        return res.status(400).json({ message: 'Missing required fields: type, productData, toNumber' });
    }

    // Check rate limiting - don't send same alert within 6 hours
    const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000);
    const checkQuery = `SELECT id FROM sms_logs WHERE client_id = ? AND type = ? AND product_name = ? AND batch_no = ? AND created_at > ?`;

    req.app.get('db').query(checkQuery, [client_id, type, productData.name, productData.batch || '', sixHoursAgo], async (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        if (results.length > 0 && !req.body.force) {
            return res.status(429).json({
                message: 'SMS recently sent for this item. Try again later or use force=true',
                recentlySent: true
            });
        }

        try {
            let result;
            let messageText;

            if (type === 'LOW_STOCK') {
                result = await sendLowStockAlertEnhanced(toNumber, productData);
                messageText = `ALERT: LOW STOCK\nProduct: ${productData.name}\nVendor: ${productData.vendor || 'N/A'}\nRemaining: ${productData.stock} ${productData.unit || 'units'}\nBatch: ${productData.batch || 'N/A'}\n- Aarambha Softwares`;
            } else if (type === 'EXPIRY') {
                result = await sendExpiryAlertEnhanced(toNumber, productData);
                messageText = `EXPIRY WARNING\nItem: ${productData.name}\nVendor: ${productData.vendor || 'N/A'}\nExpires: ${productData.expiry}\nBatch: ${productData.batch || 'N/A'}\nStock: ${productData.stock} ${productData.unit || 'units'}\n- Aarambha Softwares`;
            } else {
                return res.status(400).json({ message: 'Invalid alert type' });
            }

            // Log SMS
            const logData = {
                client_id,
                type,
                product_id: productData.id || null,
                product_name: productData.name,
                batch_no: productData.batch || '',
                vendor_name: productData.vendor || '',
                to_number: toNumber,
                message_text: messageText,
                status: result.success ? 'SENT' : 'FAILED',
                provider_response: JSON.stringify(result)
            };

            logSMS(req.app.get('db'), logData);

            if (result.success) {
                res.json({ success: true, message: 'SMS sent successfully' });
            } else {
                res.status(500).json({ success: false, error: result.error });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
});

// GET /api/sms/logs - Get SMS history
router.get('/sms/logs', requireAdmin, (req, res) => {
    const client_id = req.user.client_id;
    const { type, status, startDate, endDate, search } = req.query;

    let query = 'SELECT * FROM sms_logs WHERE client_id = ?';
    const params = [client_id];

    if (type) {
        query += ' AND type = ?';
        params.push(type);
    }
    if (status) {
        query += ' AND status = ?';
        params.push(status);
    }
    if (startDate) {
        query += ' AND DATE(created_at) >= ?';
        params.push(startDate);
    }
    if (endDate) {
        query += ' AND DATE(created_at) <= ?';
        params.push(endDate);
    }
    if (search) {
        query += ' AND (product_name LIKE ? OR batch_no LIKE ?)';
        params.push(`%${search}%`, `%${search}%`);
    }

    query += ' ORDER BY created_at DESC LIMIT 100';

    req.app.get('db').query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// GET /api/sms/settings - Get SMS settings
router.get('/sms/settings', requireAdmin, (req, res) => {
    const client_id = req.user.client_id;

    const query = 'SELECT * FROM sms_settings WHERE client_id = ?';
    req.app.get('db').query(query, [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        if (results.length === 0) {
            // Return default settings
            return res.json({
                enable_low_stock_sms: false,
                enable_expiry_sms: false,
                default_recipient: req.user.phone || '',
                expiry_alert_days: 30,
                low_stock_threshold: 10
            });
        }

        res.json(results[0]);
    });
});

// POST /api/sms/settings - Save SMS settings
router.post('/sms/settings', requireAdmin, (req, res) => {
    const client_id = req.user.client_id;
    const { enable_low_stock_sms, enable_expiry_sms, default_recipient, expiry_alert_days, low_stock_threshold } = req.body;

    const checkQuery = 'SELECT id FROM sms_settings WHERE client_id = ?';
    req.app.get('db').query(checkQuery, [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });

        if (results.length === 0) {
            // Insert new settings
            const insertQuery = `INSERT INTO sms_settings 
                (client_id, enable_low_stock_sms, enable_expiry_sms, default_recipient, expiry_alert_days, low_stock_threshold) 
                VALUES (?, ?, ?, ?, ?, ?)`;

            req.app.get('db').query(insertQuery, [
                client_id, enable_low_stock_sms, enable_expiry_sms, default_recipient, expiry_alert_days, low_stock_threshold
            ], (err) => {
                if (err) return res.status(500).json({ error: err.message });
                res.json({ message: 'Settings saved successfully' });
            });
        } else {
            // Update existing settings
            const updateQuery = `UPDATE sms_settings SET 
                enable_low_stock_sms = ?, enable_expiry_sms = ?, default_recipient = ?, 
                expiry_alert_days = ?, low_stock_threshold = ? 
                WHERE client_id = ?`;

            req.app.get('db').query(updateQuery, [
                enable_low_stock_sms, enable_expiry_sms, default_recipient, expiry_alert_days, low_stock_threshold, client_id
            ], (err) => {
                if (err) return res.status(500).json({ error: err.message });
                res.json({ message: 'Settings updated successfully' });
            });
        }
    });
});

// POST /api/sms/test - Send test SMS
router.post('/sms/test', requireAdmin, async (req, res) => {
    const { phone } = req.body;

    if (!phone) {
        return res.status(400).json({ message: 'Phone number required' });
    }

    try {
        const { sendSMS } = require('./services/sms');
        const result = await sendSMS(phone, '[Aarambha PMS] This is a test SMS. Your SMS alerts are configured correctly.');

        if (result.success) {
            res.json({ success: true, message: 'Test SMS sent successfully' });
        } else {
            res.status(500).json({ success: false, error: result.error });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// GET /api/sms/balance - Get SMS balance
router.get('/sms/balance', requireAdmin, async (req, res) => {
    try {
        const balance = await getSMSBalance();
        res.json(balance);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
