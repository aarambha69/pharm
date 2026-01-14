const cron = require('node-cron');
const { sendLowStockAlertEnhanced, sendExpiryAlertEnhanced, logSMS } = require('./services/sms');

// Auto SMS Alert Scheduler
class SMSAlertScheduler {
    constructor(db) {
        this.db = db;
        this.isRunning = false;
    }

    start() {
        if (this.isRunning) {
            console.log('SMS Alert Scheduler already running');
            return;
        }

        // Run daily at 9:00 AM
        cron.schedule('0 9 * * *', () => {
            console.log('Running daily SMS alert check...');
            this.sendDailyAlerts();
        });

        // Also run immediately on startup for testing
        setTimeout(() => {
            console.log('Running initial SMS alert check...');
            this.sendDailyAlerts();
        }, 10000); // 10 seconds after startup

        // Run Queue Processor every 2 minutes
        setInterval(() => {
            this.processOfflineQueue();
        }, 2 * 60 * 1000);

        this.isRunning = true;
        console.log('✅ SMS Alert Scheduler started (Daily at 9:00 AM + Offline Queue Processor)');
    }

    async processOfflineQueue() {
        const query = "SELECT * FROM sms_queue WHERE status = 'pending' AND retry_count < 5 LIMIT 10";
        this.db.query(query, async (err, rows) => {
            if (err || !rows.length) return;

            const { sendSMS } = require('./services/sms');

            console.log(`Processing ${rows.length} offline SMS messages...`);

            for (const row of rows) {
                try {
                    // Start processing - set timestamp?
                    const result = await sendSMS(row.to_number, row.message_text);

                    if (result.success) {
                        if (result.queued) {
                            // It failed again and created a NEW queue entry. Mark this one as resolved/replaced.
                            this.db.query("UPDATE sms_queue SET status = 'failed' WHERE id = ?", [row.id]);
                        } else {
                            this.db.query("UPDATE sms_queue SET status = 'sent', last_retry = NOW() WHERE id = ?", [row.id]);
                        }
                    } else {
                        // Failed without queuing (e.g. invalid number)
                        this.db.query("UPDATE sms_queue SET retry_count = retry_count + 1, last_retry = NOW() WHERE id = ?", [row.id]);
                    }
                } catch (e) {
                    console.error("Queue process error:", e);
                }
            }
        });
    }

    async sendDailyAlerts() {
        try {
            // Get all clients with SMS enabled
            const clientsQuery = `
                SELECT c.id, c.client_id_code, ss.default_recipient, ss.enable_low_stock_sms, ss.enable_expiry_sms, ss.expiry_alert_days, ss.low_stock_threshold
                FROM clients c
                LEFT JOIN sms_settings ss ON c.id = ss.client_id
                WHERE c.status = 'active'
            `;

            this.db.query(clientsQuery, async (err, clients) => {
                if (err) {
                    console.error('Error fetching clients for SMS alerts:', err);
                    return;
                }

                for (const client of clients) {
                    // Skip if no phone number
                    if (!client.default_recipient) continue;

                    // Check low stock alerts
                    if (client.enable_low_stock_sms) {
                        await this.checkAndSendLowStockAlerts(client);
                    }

                    // Check expiry alerts
                    if (client.enable_expiry_sms) {
                        await this.checkAndSendExpiryAlerts(client);
                    }
                }

                console.log(`✅ Daily SMS alerts processed for ${clients.length} clients`);
            });
        } catch (error) {
            console.error('Error in sendDailyAlerts:', error);
        }
    }

    async checkAndSendLowStockAlerts(client) {
        const threshold = client.low_stock_threshold || 10;

        const query = `
            SELECT s.id, m.id as medicine_id, m.name, s.batch_number, s.quantity, v.name as vendor_name
            FROM stocks s
            JOIN medicines m ON s.medicine_id = m.id
            LEFT JOIN vendors v ON s.vendor_id = v.id
            WHERE m.client_id = ? AND s.quantity < ?
            ORDER BY s.quantity ASC
            LIMIT 5
        `;

        this.db.query(query, [client.id, threshold], async (err, results) => {
            if (err || !results || results.length === 0) return;

            for (const item of results) {
                // Check if SMS was sent in last 24 hours
                const checkQuery = `SELECT id FROM sms_logs WHERE client_id = ? AND type = 'LOW_STOCK' AND product_name = ? AND batch_no = ? AND created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)`;

                this.db.query(checkQuery, [client.id, item.name, item.batch_number], async (err, logs) => {
                    if (err || logs.length > 0) return; // Skip if already sent

                    // Send SMS
                    const productData = {
                        id: item.medicine_id,
                        name: item.name,
                        vendor: item.vendor_name || 'N/A',
                        batch: item.batch_number,
                        stock: item.quantity,
                        unit: 'units'
                    };

                    try {
                        const result = await sendLowStockAlertEnhanced(client.default_recipient, productData);

                        const messageText = `ALERT: LOW STOCK\nProduct: ${productData.name}\nVendor: ${productData.vendor}\nRemaining: ${productData.stock} units\nBatch: ${productData.batch}\n- Aarambha Softwares`;

                        logSMS(this.db, {
                            client_id: client.id,
                            type: 'LOW_STOCK',
                            product_id: item.medicine_id,
                            product_name: item.name,
                            batch_no: item.batch_number,
                            vendor_name: item.vendor_name || '',
                            to_number: client.default_recipient,
                            message_text: messageText,
                            status: result.success ? 'SENT' : 'FAILED',
                            provider_response: JSON.stringify(result)
                        });

                        console.log(`✅ Low stock SMS sent to ${client.default_recipient} for ${item.name}`);
                    } catch (error) {
                        console.error(`Error sending low stock SMS:`, error);
                    }
                });
            }
        });
    }

    async checkAndSendExpiryAlerts(client) {
        const alertDays = client.expiry_alert_days || 90; // Default 3 months

        const query = `
            SELECT s.id, m.id as medicine_id, m.name, s.batch_number, s.quantity, s.expiry_date, v.name as vendor_name
            FROM stocks s
            JOIN medicines m ON s.medicine_id = m.id
            LEFT JOIN vendors v ON s.vendor_id = v.id
            WHERE m.client_id = ? AND s.expiry_date <= DATE_ADD(CURDATE(), INTERVAL ? DAY)
            ORDER BY s.expiry_date ASC
            LIMIT 5
        `;

        this.db.query(query, [client.id, alertDays], async (err, results) => {
            if (err || !results || results.length === 0) return;

            for (const item of results) {
                // Check if SMS was sent in last 24 hours
                const checkQuery = `SELECT id FROM sms_logs WHERE client_id = ? AND type = 'EXPIRY' AND product_name = ? AND batch_no = ? AND created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)`;

                this.db.query(checkQuery, [client.id, item.name, item.batch_number], async (err, logs) => {
                    if (err || logs.length > 0) return; // Skip if already sent

                    // Send SMS
                    const productData = {
                        id: item.medicine_id,
                        name: item.name,
                        vendor: item.vendor_name || 'N/A',
                        expiry: item.expiry_date.toISOString().split('T')[0],
                        batch: item.batch_number,
                        stock: item.quantity,
                        unit: 'units'
                    };

                    try {
                        const result = await sendExpiryAlertEnhanced(client.default_recipient, productData);

                        const messageText = `EXPIRY WARNING\nItem: ${productData.name}\nVendor: ${productData.vendor}\nExpires: ${productData.expiry}\nBatch: ${productData.batch}\nStock: ${productData.stock} units\n- Aarambha Softwares`;

                        logSMS(this.db, {
                            client_id: client.id,
                            type: 'EXPIRY',
                            product_id: item.medicine_id,
                            product_name: item.name,
                            batch_no: item.batch_number,
                            vendor_name: item.vendor_name || '',
                            to_number: client.default_recipient,
                            message_text: messageText,
                            status: result.success ? 'SENT' : 'FAILED',
                            provider_response: JSON.stringify(result)
                        });

                        console.log(`✅ Expiry SMS sent to ${client.default_recipient} for ${item.name}`);
                    } catch (error) {
                        console.error(`Error sending expiry SMS:`, error);
                    }
                });
            }
        });
    }
}

module.exports = SMSAlertScheduler;
