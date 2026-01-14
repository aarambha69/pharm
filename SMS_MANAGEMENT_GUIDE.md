# SMS Management System - User Guide

## Overview
The SMS Management System allows Super Admins to send SMS notifications to clients, users, and customers through the Aakash SMS API.

## Features

### 1. **Manual SMS Sending**
- Send SMS to single or multiple recipients
- Comma-separated phone numbers for bulk sending
- Character counter (160 characters limit)
- Real-time delivery status

### 2. **Excel Bulk Upload**
- Upload Excel files (.xlsx, .xls) with phone numbers
- Automatic phone number extraction
- Supported column names: `phone`, `mobile`, `number`, `contact`
- Send same message to all contacts in the file

### 3. **SMS Credit Balance**
- Real-time credit balance display
- Automatic refresh after sending
- Manual refresh button

### 4. **SMS History & Logs**
- View all sent SMS with timestamps
- Track delivery status (sent/failed)
- Statistics dashboard:
  - Total SMS sent
  - Successful deliveries
  - Failed deliveries
  - Unique recipients

## How to Use

### Manual SMS
1. Navigate to **SMS Management** from the Super Admin dashboard
2. Click on the **📝 Manual SMS** tab
3. Enter recipient phone number(s):
   - Single: `9855062769`
   - Multiple: `9855062769, 9800000000, 9841234567`
4. Type your message (max 160 characters)
5. Click **📤 SEND SMS**

### Excel Bulk Upload
1. Click on the **📊 Excel Upload** tab
2. Prepare your Excel file with a column named `phone`, `mobile`, `number`, or `contact`
3. Click **📁 SELECT EXCEL FILE** and choose your file
4. Enter the message you want to send to all recipients
5. Click **📤 SEND BULK SMS**

**Sample Excel Format:**
| phone      | name        |
|------------|-------------|
| 9855062769 | John Doe    |
| 9800000000 | Jane Smith  |
| 9841234567 | Bob Johnson |

A sample template is available at: `backend/uploads/SMS_Template.xlsx`

### View SMS History
1. Click on the **📜 SMS History** tab
2. View statistics cards showing:
   - Total SMS sent
   - Successful deliveries
   - Failed attempts
   - Unique recipients
3. Scroll through the history table to see individual SMS records

## API Configuration

The system uses **Aakash SMS API**. Configuration is stored in `.env`:

```env
AAKASH_SMS_API_KEY=your_api_key_here
```

## Phone Number Format
- Phone numbers should be 10 digits (Nepali format)
- System automatically removes non-digit characters
- Removes country code (977) if present
- Example: `9855062769` or `977-9855062769` → `9855062769`

## SMS Logs Database
All SMS are logged in the `sms_logs` table with:
- Sender information
- Recipient phone number
- Message content
- Delivery status
- Timestamp
- Error messages (if failed)

## Troubleshooting

### "Balance Unavailable" Error
- Check if `AAKASH_SMS_API_KEY` is configured in `.env`
- Verify API key is valid
- Ensure backend server is running

### "Failed to send SMS" Error
- Verify phone numbers are in correct format (10 digits)
- Check SMS credit balance
- Review error message in SMS History

### Excel Upload Issues
- Ensure Excel file has a column named: `phone`, `mobile`, `number`, or `contact`
- Phone numbers must be at least 10 digits
- File format must be `.xlsx` or `.xls`

## Best Practices
1. **Test First**: Send a test SMS to your own number before bulk sending
2. **Character Limit**: Keep messages under 160 characters to avoid splitting
3. **Verify Numbers**: Double-check phone numbers before sending
4. **Monitor Credits**: Regularly check SMS balance
5. **Review History**: Check SMS History to verify delivery status

## Support
For issues or questions, contact the development team or refer to the Aakash SMS API documentation.
