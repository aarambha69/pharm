# Client Installation Guide

## 1. Prerequisites (Required on Client PC)
Before installing the software, ensure the client PC has the following installed:

1.  **Node.js (Required for Backend)**
    *   Download and install the "LTS" version from [nodejs.org](https://nodejs.org/).
    *   During installation, just click "Next" through all defaults.

2.  **MySQL Server (Required for Database)**
    *   Install MySQL Community Server.
    *   **Important**: During setup, set the Root Password to `1234` (or update the `.env` file later if you choose a different one).
    *   Make sure the MySQL service is running.

---

## 2. Installation Steps

1.  **Copy the Application Folder**
    *   Copy the entire `AarambhaPMS_Client` folder (from your `dist` build) to the client PC (e.g., to `D:\PharmacySoftware`).

2.  **Setup the Database**
    *   Open the `backend` folder inside the installation directory.
    *   Double-click `SETUP_DB.bat` (if created) or run the following command in a terminal inside the backend folder:
        ```cmd
        node setup_complete_db.js
        ```
    *   *Note: This will create the database and all necessary tables.*

3.  **Start the Application**
    *   Double-click `AarambhaPMS.exe` to run the software.
    *   The backend server window should open automatically. **Do not close this black window**, or the system will stop working.

---

## 3. Troubleshooting

### ❌ Error: "Connection Error (Port 5000)" or "Cannot connect to server"

This means the backend server failed to start.

**Solution:**
1.  **Check the Database**: Ensure MySQL is running.
2.  **Check for Missing Columns**: The system now has a "Self-Healing" feature.
    *   Restart the application.
    *   Watch the backend console window. It will say "Checking Database Integrity..." and "Auto-fixed" if it finds any missing columns.
3.  **Check Port Conflict**: Ensure no other application is using Port 5000.
    *   Restart the PC to clear up any stuck processes.

### ❌ Error: "System Locked"
This is normal for a new installation. You need to activate it using the Super Admin key generator.
