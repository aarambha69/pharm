# Aarambha Softwares - Pharmacy Management System

## 🎯 Complete Desktop Application (.exe)

### Features Implemented:
✅ **Windows Desktop Application** - Standalone .exe file  
✅ **SMS Alerts** - Password reset, Low stock, Expiry warnings  
✅ **Machine-Bound Licensing** - Hardware-locked activation  
✅ **Modern UI** - CustomTkinter with dark/light themes  
✅ **A5 Bill Printing** - Professional invoice generation  
✅ **Role-Based Access** - Super Admin → Admin → Cashier  
✅ **MySQL Database** - Secure data storage  

---

## 🚀 Quick Start

### Option 1: Run Desktop App (Development)
```bash
cd DesktopApp
RUN.bat
```

### Option 2: Build Standalone .exe
```bash
cd DesktopApp
BUILD.bat
```
The .exe will be created in `DesktopApp/dist/AarambhaPMS.exe`

---

## 📋 Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **MySQL Server** - Already configured

---

## 🔐 Super Admin Login

- **Phone**: `9855062769`
- **Password**: `987654321`

---

## 📱 SMS Configuration

To enable SMS alerts (password reset, low stock, expiry):

1. Sign up at [Twilio](https://www.twilio.com/try-twilio)
2. Get your Account SID, Auth Token, and Phone Number
3. Update `backend/.env`:
```
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE=+1234567890
```

---

## 🎨 Desktop App Features

### Login Screen
- Modern split-screen design
- Machine ID display
- "Forgot Password? Reset via SMS" button

### Super Admin Dashboard
- Client management
- License monitoring
- Package builder
- Global alerts
- System settings

### Admin Dashboard
- Daily sales tracking
- Low stock warnings (SMS alerts)
- Expiry monitoring (SMS alerts)
- Staff management
- Reports

### Cashier Billing Terminal
- Fast medicine search
- A5 bill printing
- VAT & discount calculation
- Real-time inventory updates

---

## 📊 Database Schema

All tables created in `database/schema.sql`:
- `users` - Authentication & roles
- `clients` - Pharmacy accounts
- `packages` - Subscription plans
- `medicines` - Inventory items
- `stocks` - Batch & expiry tracking
- `sales` - Transaction records
- `vendors` - Supplier management

---

## 🛠️ Tech Stack

**Desktop App**: Python + CustomTkinter  
**Backend**: Node.js + Express  
**Database**: MySQL  
**SMS**: Twilio API  
**Licensing**: Machine ID binding  

---

## 📞 Support

For issues or customization:
- Email: aarambhaaryal.dev@gmail.com
- Phone: 9855062769

---

**Aarambha Softwares © 2026**  
*Protected by Shield™ Technology*
