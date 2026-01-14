const axios = require('axios');
const https = require('https');

// Aakash SMS Configuration
const AAKASH_API_KEY = process.env.AAKASH_SMS_API_KEY;
let globalDB = null;

// Official Aakash SMS API endpoints
const AAKASH_API_URL = 'https://sms.aakashsms.com/sms/v3/send';
const AAKASH_BALANCE_URL = 'https://sms.aakashsms.com/sms/v1/credit';

// Create axios instance with SSL bypass to handle aakashsms.com cert issues
const axiosInstance = axios.create({
    httpsAgent: new https.Agent({
        rejectUnauthorized: false
    }),
    timeout: 30000 // 30 second timeout
});

if (!AAKASH_API_KEY) {
    console.log('⚠️ Aakash SMS API Key not configured.');
}

/**
 * Get SMS Credit Balance
 */
const getSMSBalance = async () => {
    if (!AAKASH_API_KEY) {
        return { success: false, error: 'API key not configured', balance: 0 };
    }

    try {
        const params = new URLSearchParams();
        params.append('auth_token', AAKASH_API_KEY);

        const response = await axiosInstance.post(AAKASH_BALANCE_URL, params);

        if (response.data && (response.data.available_credit !== undefined || response.data.balance !== undefined)) {
            return {
                success: true,
                balance: response.data.available_credit || response.data.balance,
                currency: 'Credits'
            };
        }

        return { success: false, error: 'Internal API Error', balance: 0 };
    } catch (error) {
        console.error('SMS Balance Error:', error.message);
        return { success: false, error: 'Gateway Timeout/Offline', balance: 0 };
    }
};

/**
 * Send Single SMS via Aakash SMS
 */
const sendSMS = async (to, message) => {
    if (!AAKASH_API_KEY) {
        console.log(`[SMS Simulation] To: ${to}, Msg: ${message}`);
        return { success: true, simulated: true };
    }

    try {
        // Format phone number (remove +977 if present, ensure 10 digits)
        let phone = to.replace(/\D/g, ''); // Remove non-digits
        if (phone.startsWith('977')) {
            phone = phone.substring(3);
        }
        if (phone.length !== 10) {
            return { success: false, error: 'Invalid phone number format. Must be 10 digits.' };
        }

        const payload = {
            auth_token: AAKASH_API_KEY,
            to: phone,
            text: message
        };

        const response = await axiosInstance.post(AAKASH_API_URL, payload, {
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: 10000
        });

        console.log('SMS Send Response:', response.data);

        // Aakash SMS v3 returns { error: false, message: "..." } on success
        // Some versions might still return { status: "success" }
        const isSuccess = response.data && (response.data.status === 'success' || response.data.error === false);

        if (isSuccess) {
            const msgId = response.data.message_id || (response.data.data && response.data.data.valid && response.data.data.valid[0] && response.data.data.valid[0].id);
            console.log(`✅ SMS sent to ${phone}: ${msgId || 'OK'}`);
            return {
                success: true,
                messageId: msgId,
                recipient: phone,
                message: 'SMS sent successfully'
            };
        }

        return {
            success: false,
            error: response.data.message || 'Failed to send SMS'
        };

    } catch (error) {
        console.error('SMS Error:', error.response?.data || error.message);

        // Auto-Queue if network/server error and DB available
        if (globalDB && (error.code === 'ENOTFOUND' || error.code === 'ETIMEDOUT' || error.code === 'ECONNREFUSED' || !error.response)) {
            try {
                queueSMS(to, message);
                return { success: true, queued: true, message: 'Offline: SMS Queued' };
            } catch (qErr) {
                console.error('Queue Error:', qErr);
            }
        }

        return {
            success: false,
            error: error.response?.data?.message || error.message
        };
    }
};

/**
 * Send Bulk SMS to multiple recipients
 */
const sendBulkSMS = async (recipients, message) => {
    if (!AAKASH_API_KEY) {
        console.log(`[SMS Simulation] Bulk SMS to ${recipients.length} recipients`);
        return {
            success: true,
            simulated: true,
            sent: recipients.length,
            failed: 0
        };
    }

    const results = {
        total: recipients.length,
        sent: 0,
        failed: 0,
        details: []
    };

    for (const recipient of recipients) {
        const result = await sendSMS(recipient, message);

        if (result.success) {
            results.sent++;
            results.details.push({
                phone: recipient,
                status: 'sent',
                messageId: result.messageId
            });
        } else {
            results.failed++;
            results.details.push({
                phone: recipient,
                status: 'failed',
                error: result.error
            });
        }

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    return {
        success: true,
        ...results
    };
};

// Password reset SMS
const sendPasswordResetSMS = async (phone, resetCode) => {
    const message = `[Aarambha PMS] Your password reset code is: ${resetCode}. Valid for 10 minutes. Do not share this code.`;
    return await sendSMS(phone, message);
};

// Low stock alert SMS
const sendLowStockAlert = async (phone, medicineName, currentStock) => {
    const message = `[Aarambha PMS] ⚠️ LOW STOCK ALERT: ${medicineName} has only ${currentStock} units remaining. Please reorder immediately.`;
    return await sendSMS(phone, message);
};

// Expiry alert SMS
const sendExpiryAlert = async (phone, medicineName, expiryDate) => {
    const message = `[Aarambha PMS] ⏰ EXPIRY WARNING: ${medicineName} will expire on ${expiryDate}. Take necessary action.`;
    return await sendSMS(phone, message);
};

// License expiry alert
const sendLicenseExpiryAlert = async (phone, pharmacyName, daysLeft) => {
    const message = `[Aarambha PMS] 🔐 LICENSE ALERT: ${pharmacyName} license expires in ${daysLeft} days. Renew now to avoid service interruption.`;
    return await sendSMS(phone, message);
};

// Welcome SMS for new clients
const sendWelcomeSMS = async (phone, pharmacyName, password) => {
    const message = `[Aarambha PMS] Welcome ${pharmacyName}! Your account is ready. Login: ${phone}, Password: ${password}. Change your password after first login.`;
    return await sendSMS(phone, message);
};

// Enhanced Low Stock Alert SMS (with vendor and batch info)
const sendLowStockAlertEnhanced = async (phone, productData) => {
    const message = `ALERT: LOW STOCK
Product: ${productData.name}
Vendor: ${productData.vendor || 'N/A'}
Remaining: ${productData.stock} ${productData.unit || 'units'}
Batch: ${productData.batch || 'N/A'}
- Aarambha Softwares`;
    return await sendSMS(phone, message);
};

// Enhanced Expiry Alert SMS (with vendor and batch info)
const sendExpiryAlertEnhanced = async (phone, productData) => {
    const message = `EXPIRY WARNING
Item: ${productData.name}
Vendor: ${productData.vendor || 'N/A'}
Expires: ${productData.expiry}
Batch: ${productData.batch || 'N/A'}
Stock: ${productData.stock} ${productData.unit || 'units'}
- Aarambha Softwares`;
    return await sendSMS(phone, message);
};

// Daily Summary SMS
const sendDailySummarySMS = async (phone, summaryData) => {
    const message = `DAILY ALERT SUMMARY
Low Stock: ${summaryData.lowStockCount}
Expiry Soon (${summaryData.alertDays}d): ${summaryData.expirySoonCount}
Expired: ${summaryData.expiredCount}
- Aarambha Softwares`;
    return await sendSMS(phone, message);
};

// Log SMS to database
const logSMS = (db, logData) => {
    if (!db) return;
    const { client_id, type, product_id, product_name, batch_no, vendor_name, to_number, message_text, status, provider_response } = logData;

    const query = `INSERT INTO sms_logs 
        (client_id, type, product_id, product_name, batch_no, vendor_name, to_number, message_text, status, provider_response) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;

    db.query(query, [
        client_id, type, product_id, product_name, batch_no, vendor_name,
        to_number, message_text, status, provider_response || ''
    ], (err) => {
        if (err) console.error('SMS Log Error:', err);
    });
};

// Queue SMS for retry
const queueSMS = (to, message) => {
    if (!globalDB) return false;
    console.log(`⚠️ Offline/API Error: Queuing SMS to ${to}`);
    const query = 'INSERT INTO sms_queue (to_number, message_text, status, created_at) VALUES (?, ?, "pending", NOW())';
    globalDB.query(query, [to, message], (err) => {
        if (err) console.error('Failed to queue SMS:', err);
    });
    return true;
};

module.exports = {
    setDB: (db) => { globalDB = db; },
    sendSMS,
    sendBulkSMS,
    getSMSBalance,
    sendPasswordResetSMS,
    sendLowStockAlert,
    sendExpiryAlert,
    sendLicenseExpiryAlert,
    sendWelcomeSMS,
    sendLowStockAlertEnhanced,
    sendExpiryAlertEnhanced,
    sendDailySummarySMS,
    logSMS
};
