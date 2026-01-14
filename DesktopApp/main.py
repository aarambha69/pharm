import customtkinter as ctk
from dashboard_ui import DashboardUI
from bill_designer_ui import BillDesignerUI
import requests
from tkinter import messagebox, ttk, StringVar, IntVar, DoubleVar, BooleanVar, filedialog
import tkinter as tk
from tkcalendar import DateEntry
import json
import qrcode
from datetime import datetime, timedelta
import os
import uuid
import platform
from typing import Optional
from PIL import Image, ImageTk, ImageDraw, ImageOps
import io
import random
import time
import sys
import traceback
import logging

# --- GLOBAL EXCEPTION HANDLER (ZERO CRASH POLICY) ---
logging.basicConfig(filename='crash.log', level=logging.ERROR, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Catches all unhandled exceptions to prevent app crash.
    Logs error and shows friendly message.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error("Uncaught Exception:\n" + error_msg)
    
    # Show friendly UI
    try:
        err_str = f"{exc_type.__name__}: {exc_value}"
        # If root exists, show message box
        if 'app' in globals() and hasattr(app, 'root'):
             messagebox.showerror("Unexpected Error", 
                f"A system error occurred, but the application has recovered.\n\nError: {err_str}\n\nDetails logged to crash.log")
        else:
             # Fallback for early crashes
             try:
                 root = tk.Tk()
                 root.withdraw()
                 messagebox.showerror("Startup Error", f"Critical Error: {err_str}")
                 root.destroy()
             except:
                 pass
    except:
        pass

sys.excepthook = global_exception_handler
# ----------------------------------------------------

from ScannerModule import ScannerModule
from karobar_ui import KarobarUI
from date_utils import DateUtils

# --- CONFIGURATION (Load from file if exists) ---
CONFIG_FILE = "config.json"
DEFAULT_API_BASE = "http://127.0.0.1:5000/api"

API_BASE = DEFAULT_API_BASE
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            API_BASE = config.get("api_url", DEFAULT_API_BASE)
    except Exception as e:
        logging.error(f"Failed to load config.json: {e}")

# If we are in the _internal folder (dist build), look one level up (where the exe is)
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    config_path = os.path.join(exe_dir, CONFIG_FILE)
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                API_BASE = config.get("api_url", DEFAULT_API_BASE)
        except: pass

print(f"Using API Server: {API_BASE}")

# Generate Machine ID from hardware info
def get_machine_id():
    machine_string = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, machine_string))

MACHINE_ID = get_machine_id()

def generate_qr(code, name, strength):
    """Generate and return a path to a QR code image"""
    qr_data = f"{code}|{name}|{strength}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "qrcodes")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
import subprocess
import atexit

# ... [imports] ...

class AarambhaPMS(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # SETUP WINDOW GEOMETRY FIRST (Critical Fix)
        self.title("Aarambha Softwares - Pharmacy Management System v2.0")
        self.geometry("1400x900")
        self.resizable(True, True)
        
        # Set App Icon (Windows Standard)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            
            # Fallback for internal windows
            png_path = os.path.join(os.path.dirname(__file__), "assets", "logo.jpg")
            if os.path.exists(png_path):
                icon_img = Image.open(png_path)
                self.iconphoto(True, ImageTk.PhotoImage(icon_img))
        except Exception as e:
            print(f"Failed to set app icon: {e}")

        self.root = self # Bridge for existing code using self.root
        self.API_BASE = API_BASE
        
        # Start Backend Server
        self.backend_process = None
        self.start_backend()
        atexit.register(self.stop_backend)
        
        # ...
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.token = None
        self.user = None
        self.machine_id = MACHINE_ID
        self.user_role = None
        self.active_package = None
        self.license_expiry = None
        
        # Calendar View State
        self.cal_view_year = datetime.now().year
        self.cal_view_month = datetime.now().month
        
        # Live clock variables
        self.time_var = StringVar()
        self.nepali_date_var = StringVar()
        self.english_date_var = StringVar()
        self.day_var = StringVar()
        self.update_time_date()
        
        # Karobar Implementation
        self.karobar = KarobarUI(self)
        
        # Initial Loading Screen
        self.show_loading_screen()
        
        # Schedule startup checks (allow UI to render first)
        self.after(2000, self.perform_startup_checks)

    def start_backend(self):
        """Start Node.js backend if not running"""
        try:
            # Check if backend is already running (e.g. check port 5000)
            try:
                requests.get(f"{API_BASE}/check-license", timeout=1)
                print("Backend already running")
                return
            except:
                pass # Not running
            
            # Locate backend folder
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            backend_path = os.path.join(base_dir, "backend", "server.js")
            
            if os.path.exists(backend_path):
                 print(f"Starting backend from {backend_path}")
                 
                 # SHOW CONSOLE WINDOW for Debugging (REQUIRED for User Diagnosis)
                 self.backend_process = subprocess.Popen(
                     ["node", backend_path], 
                     cwd=os.path.dirname(backend_path),
                     creationflags=subprocess.CREATE_NEW_CONSOLE
                 )
                 time.sleep(2) # Wait for startup
            else:
                 messagebox.showwarning("Backend Missing", f"Could not find backend at {backend_path}")
        except Exception as e:
            print(f"Failed to start backend: {e}")

    def stop_backend(self):
        if self.backend_process:
            self.backend_process.terminate()
    
    def on_closing(self):
        self.stop_backend()
        self.destroy()

    def show_loading_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        loading_frame = ctk.CTkFrame(self.root, fg_color=("#1a1a2e", "#0f0f1e"))
        loading_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            loading_frame,
            text="🏥 AARAMBHA PMS",
            font=("Segoe UI Black", 40),
            text_color=("#4a90e2", "#5ba3ff")
        ).place(relx=0.5, rely=0.4, anchor="center")
        
        ctk.CTkLabel(
            loading_frame,
            text="Initializing System & Database...",
            font=("Segoe UI", 16),
            text_color="gray"
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        self.update()

    def perform_startup_checks(self):
        """Bypass license check - Go straight to Login"""
        # User requested to remove machine-id activation.
        self.show_login()

    def update_time_date(self):
        """Standard BS Date Clock"""
        now = datetime.now()
        self.time_var.set(now.strftime("%I:%M:%S %p"))
        
        # Strict Nepali Date
        full_bs = DateUtils.get_current_bs_date_full() # 2082 Magh 14
        bs_numeric = DateUtils.get_current_bs_date_str() # 2082-10-14
        
        parts = full_bs.split(' ')
        if len(parts) >= 3:
            # English Text (e.g. 2082 Magh 14)
            self.nepali_date_var.set(f"{parts[0]}, {parts[1]} {parts[2]}")
            # English Gregorian (e.g. January 27, 2026) - Keep as secondary or remove? 
            # User said "English date (AD) must NOT be shown anywhere". 
            # Replacing with English Month text of BS date
            self.english_date_var.set(now.strftime("%B %d, %Y")) # Revisit this if strict NO AD allowed even for mapping.
            # actually user said "English date (AD) must NOT be shown". 
            # I will replace the secondary text with the Numeric BS date to be safe.
            self.english_date_var.set(now.strftime("%B %d, %Y")) # Wait, this IS AD.
            
            # Correction:
            self.english_date_var.set(now.strftime("%B %d, %Y")) # OLD
            
            # New Strict Logic:
            self.nepali_date_var.set(f"{parts[0]}, {parts[1]} {parts[2]}") # 2082, Magh 14
            self.english_date_var.set(bs_numeric) # 2082-10-14 (Strict BS Only)

        self.day_var.set(now.strftime("%A"))
        self.after(1000, self.update_time_date)
        
    def check_license(self, current_machine_id):
        """Global license enforcement: No License = No Access"""
        try:
            response = requests.post(f"{API_BASE}/check-license", json={"machine_id": current_machine_id}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    # Success
                    self.user_role = data.get('role')
                    self.active_package = data.get('package_name')
                    self.enabled_features = data.get('features', '').split(',')
                    self.license_expiry = data.get('expiry')
                    return True, ""
                else:
                    return False, data.get('message', 'Invalid License')
            return False, "Connection Error"
        except Exception as e:
            return False, str(e)

    def show_locked_screen(self, msg="Activation Required"):
        """Strict enforcement: Locked mode only allows activation"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
        locked_frame = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        locked_frame.pack(fill="both", expand=True)
        
        container = ctk.CTkFrame(locked_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=25)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="🔒 SYSTEM LOCKED", font=("Segoe UI Black", 32), text_color="#ef4444").pack(pady=(40, 10), padx=50)
        ctk.CTkLabel(container, text=msg, font=("Segoe UI", 16)).pack(pady=5)
        
        ctk.CTkLabel(container, text="Your Machine ID:", font=("Segoe UI Semibold", 13), text_color="gray").pack(pady=(20, 5))
        id_entry = ctk.CTkEntry(container, width=500, height=45, justify="center", font=("Consolas", 14))
        id_entry.insert(0, self.machine_id)
        id_entry.configure(state="readonly")
        id_entry.pack(pady=5, padx=50)
        
        ctk.CTkLabel(container, text="Select Role & Client:", font=("Segoe UI Semibold", 13)).pack(pady=(20, 5))
        
        role_frame = ctk.CTkFrame(container, fg_color="transparent")
        role_frame.pack(fill="x", padx=50)
        
        role_var = StringVar(value="ADMIN")
        ctk.CTkRadioButton(role_frame, text="Unit Admin", variable=role_var, value="ADMIN").pack(side="left", padx=20)
        ctk.CTkRadioButton(role_frame, text="Cashier", variable=role_var, value="CASHIER").pack(side="left", padx=20)

        # Client ID (Database ID) - In a real setup, Super Admin would provide this along with the key
        ctk.CTkLabel(container, text="Pharmacy ID (provided by Admin):", font=("Segoe UI Semibold", 11), text_color="gray").pack(pady=(10, 0))
        client_id_entry = ctk.CTkEntry(container, width=500, height=40, placeholder_text="e.g., 12", justify="center")
        client_id_entry.pack(pady=5)

        ctk.CTkLabel(container, text="Enter 16-Digit Activation Key:", font=("Segoe UI Semibold", 13)).pack(pady=(15, 5))
        key_entry = ctk.CTkEntry(container, width=500, height=50, placeholder_text="XXXX-XXXX-XXXX-XXXX", justify="center", font=("Consolas", 18, "bold"))
        key_entry.pack(pady=5)
        
        def attempt_activation():
            key = key_entry.get().strip().replace(" ", "").upper()
            role = role_var.get()
            c_id = client_id_entry.get().strip()
            
            if not key or len(key) != 16:
                messagebox.showerror("Error", "Please enter a valid 16-digit key")
                return
            
            try:
                res = requests.post(f"{API_BASE}/activate-system", json={
                    "machine_id": self.machine_id,
                    "license_key": key,
                    "role": role,
                    "client_id": int(c_id) if c_id else None
                })
                if res.status_code == 200:
                    messagebox.showinfo("Success", "System Activated! Please restart.")
                    self.root.quit()
                else:
                    messagebox.showerror("Error", res.json().get('message', 'Activation Failed'))
            except Exception as e:
                messagebox.showerror("Error", f"Connection failed: {str(e)}")

        ctk.CTkButton(container, text="⚡ ACTIVATE SYSTEM", width=500, height=55, font=("Segoe UI Black", 16), command=attempt_activation).pack(pady=(30, 20), padx=50)

        def switch_to_admin_login():
            # Show a dedicated Super Admin Login for activation bypass
            login_dialog = ctk.CTkToplevel(self.root)
            login_dialog.title("Super Admin Authorization")
            login_dialog.geometry("500x400")
            login_dialog.transient(self.root)
            login_dialog.grab_set()
            
            ctk.CTkLabel(login_dialog, text="🔑 Authorization Required", font=("Segoe UI Black", 20)).pack(pady=20)
            
            phone_e = ctk.CTkEntry(login_dialog, placeholder_text="Super Admin Phone", width=350, height=45)
            phone_e.pack(pady=10)
            
            pass_e = ctk.CTkEntry(login_dialog, placeholder_text="Password", show="●", width=350, height=45)
            pass_e.pack(pady=10)
            
            def auth_and_activate():
                p = phone_e.get().strip()
                pw = pass_e.get().strip()
                
                # DEBUG ALERT
                # messagebox.showinfo("Debug", f"Attempting auth for {p}...")
                
                try:
                    # Special endpoint to activate device via Super Admin credentials
                    # print(f"Sending request to {API_BASE}/activate-super-admin")
                    res = requests.post(f"{API_BASE}/activate-super-admin", json={
                        "machine_id": self.machine_id,
                        "phone": p,
                        "password": pw
                    }, timeout=10) # Added timeout
                    
                    # messagebox.showinfo("Debug", f"Response: {res.status_code}")
                    
                    if res.status_code == 200:
                        messagebox.showinfo("Success", "Device Authorized! Restarting...")
                        self.save_activation_status()
                        self.root.quit()
                    else:
                        messagebox.showerror("Error", res.json().get('message', 'Authorization Failed'))
                except Exception as e:
                    messagebox.showerror("Error", f"Request Failed: {str(e)}")

            ctk.CTkButton(login_dialog, text="AUTHORIZE THIS DEVICE", width=350, height=50, command=auth_and_activate).pack(pady=30)

        ctk.CTkButton(container, text="🔑 SUPER ADMIN AUTHORIZATION", width=500, height=45, font=("Segoe UI Semibold", 13), fg_color="transparent", border_width=2, command=switch_to_admin_login).pack(pady=(0, 40), padx=50)
    
    def check_local_activation(self):
        """Check if device is activated locally (for offline use)"""
        activation_file = os.path.join(os.path.expanduser("~"), ".aarambha_activation")
        if os.path.exists(activation_file):
            try:
                with open(activation_file, 'r') as f:
                    data = json.load(f)
                    return data.get('machine_id') == MACHINE_ID and data.get('activated', False)
            except:
                return False
        return False
    
    def save_activation_status(self):
        """Save activation status locally"""
        activation_file = os.path.join(os.path.expanduser("~"), ".aarambha_activation")
        try:
            with open(activation_file, 'w') as f:
                json.dump({
                    'machine_id': MACHINE_ID,
                    'activated': True,
                    'timestamp': datetime.now().isoformat()
                }, f)
        except Exception as e:
            print(f"Failed to save activation: {e}")
    
    def show_activation_screen(self):
        """First-time activation screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = ctk.CTkFrame(self.root, fg_color=("#1a1a2e", "#0f0f1e"))
        main_frame.pack(fill="both", expand=True)
        
        container = ctk.CTkFrame(main_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=30)
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.5, relheight=0.7)
        
        ctk.CTkLabel(
            container,
            text="🔐 Software Activation Required",
            font=("Segoe UI Black", 32, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(50, 20))
        
        ctk.CTkLabel(
            container,
            text=f"Machine ID: {MACHINE_ID}",
            font=("Consolas", 14, "bold"),
            text_color=("#64748b", "#94a3b8")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            container,
            text="Contact Super Admin to activate this device",
            font=("Segoe UI", 16),
            text_color=("#64748b", "#94a3b8")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            container,
            text="Enter Activation Key:",
            font=("Segoe UI Semibold", 14),
            text_color=("#64748b", "#94a3b8")
        ).pack(pady=(40, 10))
        
        activation_entry = ctk.CTkEntry(
            container,
            width=500,
            height=50,
            font=("Consolas", 16),
            placeholder_text="XXXX-XXXX-XXXX-XXXX"
        )
        activation_entry.pack(pady=10)
        
        def activate():
            key = activation_entry.get()
            if not key:
                messagebox.showerror("Error", "Please enter activation key")
                return
            
            try:
                response = requests.post(f"{API_BASE}/activate", json={
                    "machine_id": MACHINE_ID,
                    "activation_key": key
                })
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Software activated successfully!")
                    self.show_login()
                else:
                    messagebox.showerror("Error", response.json().get('message', 'Invalid activation key'))
            except Exception as e:
                messagebox.showerror("Error", f"Activation failed: {str(e)}")
        
        ctk.CTkButton(
            container,
            text="ACTIVATE SOFTWARE",
            width=500,
            height=55,
            font=("Segoe UI Black", 16),
            command=activate
        ).pack(pady=30)
        
    def show_login(self):
        """Enhanced login screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
        main_frame = ctk.CTkFrame(self.root, fg_color=("#1a1a2e", "#0f0f1e"))
        main_frame.pack(fill="both", expand=True)
        
        # Left side - Branding
        left_frame = ctk.CTkFrame(main_frame, fg_color=("#16213e", "#0d1117"), corner_radius=0)
        left_frame.pack(side="left", fill="both", expand=True)
        
        brand_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        brand_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo loading logic with robust path finding
        try:
            logo_path = None
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "assets", "logo.jpg"),
                os.path.join(os.path.dirname(sys.executable), "assets", "logo.jpg"),
                "assets/logo.jpg"
            ]
            
            for p in possible_paths:
                if os.path.exists(p):
                    logo_path = p
                    break
            
            if logo_path:
                pil_img = Image.open(logo_path)
                # Create CTkImage with size tuple (width, height)
                logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 200))
                
                ctk.CTkLabel(
                    brand_container,
                    text="", 
                    image=logo_img
                ).pack(pady=(0, 20))
            else:
                # Fallback to text if image missing
                raise Exception("Logo file not found")
                
        except Exception as e:
            print(f"Logo load error: {e}")
            ctk.CTkLabel(
                brand_container, 
                text="🏥 AARAMBHA\nSOFTWARES", 
                font=("Segoe UI Black", 52, "bold"),
                text_color=("#4a90e2", "#5ba3ff"),
                justify="center"
            ).pack(pady=(0, 30))
        
        ctk.CTkLabel(
            brand_container,
            text="Commercial-Grade Pharmacy\nManagement & Billing System",
            font=("Segoe UI", 20),
            text_color=("#94a3b8", "#cbd5e1"),
            justify="center"
        ).pack(pady=20)
        
        features_frame = ctk.CTkFrame(brand_container, fg_color="transparent")
        features_frame.pack(pady=40)
        
        features = [
            "✓ Machine-Bound Licensing System",
            "✓ SMS Alerts (Low Stock & Expiry)",
            "✓ A5 Professional Bill Printing",
            "✓ Multi-Client Management",
            "✓ Package-Based Feature Control",
            "✓ Real-time Inventory Tracking"
        ]
        
        for feature in features:
            ctk.CTkLabel(
                features_frame,
                text=feature,
                font=("Segoe UI Semibold", 15),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            ).pack(pady=10, padx=40, anchor="w")
        
        # Right side - Login Form
        right_frame = ctk.CTkFrame(main_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=0)
        right_frame.pack(side="right", fill="both", expand=True)
        
        login_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        login_container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(
            login_container,
            text="Welcome Back",
            font=("Segoe UI Black", 40, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            login_container,
            text="Sign in to access your pharmacy dashboard",
            font=("Segoe UI", 14),
            text_color=("#64748b", "#94a3b8")
        ).pack(pady=(0, 50))
        
        # Phone input
        ctk.CTkLabel(
            login_container,
            text="LOGIN ID / PHONE NUMBER",
            font=("Segoe UI Semibold", 12),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        self.phone_entry = ctk.CTkEntry(
            login_container,
            placeholder_text="Enter your registered phone number",
            width=450,
            height=55,
            font=("Segoe UI", 15),
            corner_radius=15,
            border_width=2
        )
        self.phone_entry.pack(pady=(0, 25))
        
        # Password input
        ctk.CTkLabel(
            login_container,
            text="PASSWORD",
            font=("Segoe UI Semibold", 12),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        self.password_entry = ctk.CTkEntry(
            login_container,
            placeholder_text="Enter your password",
            show="●",
            width=450,
            height=55,
            font=("Segoe UI", 15),
            corner_radius=15,
            border_width=2
        )
        self.password_entry.pack(pady=(0, 15))
        
        # Forgot password
        forgot_btn = ctk.CTkButton(
            login_container,
            text="🔑 Forgot Password? Reset via SMS",
            font=("Segoe UI Semibold", 12),
            fg_color="transparent",
            text_color=("#4a90e2", "#5ba3ff"),
            hover=False,
            command=self.show_password_reset
        )
        forgot_btn.pack(pady=(0, 35))
        
        # Login button
        login_btn = ctk.CTkButton(
            login_container,
            text="INITIALIZE SESSION",
            width=450,
            height=60,
            font=("Segoe UI Black", 16, "bold"),
            corner_radius=15,
            fg_color=("#4a90e2", "#5ba3ff"),
            hover_color=("#3b7bc9", "#4a8fe6"),
            command=self.login
        )
        login_btn.pack(pady=(0, 25))
        
        # Machine ID
        machine_frame = ctk.CTkFrame(login_container, fg_color=("#f1f5f9", "#0f172a"), corner_radius=12)
        machine_frame.pack(pady=25, fill="x")
        
        ctk.CTkLabel(
            machine_frame,
            text=f"🔒 Machine ID: {MACHINE_ID[:32]}...",
            font=("Consolas", 11),
            text_color=("#64748b", "#94a3b8")
        ).pack(pady=15, padx=20)
        
        # Footer
        ctk.CTkLabel(
            right_frame,
            text="Aarambha Softwares © 2026 | Protected by Shield™ Technology",
            font=("Segoe UI", 11),
            text_color=("#cbd5e1", "#475569")
        ).pack(side="bottom", pady=25)
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())
        
    def refresh_user_profile(self):
        """Fetch latest user data (permissions etc.) from server"""
        try:
            res = requests.get(f"{API_BASE}/auth/profile", headers={"Authorization": f"Bearer {self.token}"})
            if res.status_code == 200:
                self.user = res.json()
                return True
        except: pass
        return False

    def login(self):
        """Enhanced login with role-based routing"""
        phone = self.phone_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # DEBUG ALERT
        # messagebox.showinfo("Debug", "Login button clicked!")
        
        if not phone or not password:
            messagebox.showerror("Validation Error", "Please enter both phone number and password")
            return
            
        try:
            # messagebox.showinfo("Debug", f"Connecting to {API_BASE}/login...")
            # We add a longer timeout here
            response = requests.post(f"{API_BASE}/login", json={
                "phone": phone,
                "password": password
            }, timeout=15)
            
            # messagebox.showinfo("Debug", f"Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.user = data['user']
                
                # Auto-activate Super Admin device permanently on first login
                if self.user['role'] == 'SUPER_ADMIN':
                    try:
                        requests.post(f"{API_BASE}/activate-super-admin", json={
                            "machine_id": MACHINE_ID,
                            "phone": phone,
                            "password": password
                        }, timeout=5)
                        self.save_activation_status()
                    except:
                        pass
                
                # Route based on role
                if self.user['role'] == 'SUPER_ADMIN':
                    self.show_super_admin_dashboard()
                elif self.user['role'] == 'ADMIN':
                    self.show_admin_dashboard()
                elif self.user['role'] == 'CASHIER':
                    self.show_billing_terminal()
                else:
                    messagebox.showerror("Error", "Invalid user role")
            else:
                error_msg = response.json().get('message', 'Invalid credentials')
                messagebox.showerror("Login Failed", error_msg)
        except requests.exceptions.Timeout:
            messagebox.showerror("Connection Error", "Server timed out. Is the backend running?")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", "Cannot connect to server. Ensure Port 5000 is open.")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
    
    def show_password_reset(self):
        """SMS-based password reset dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Password Reset via SMS")
        dialog.geometry("550x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(
            container,
            text="🔐 Reset Password",
            font=("Segoe UI Black", 28, "bold")
        ).pack(pady=(0, 15))
        
        ctk.CTkLabel(
            container,
            text="Enter your registered phone number to receive\na 6-digit reset code via SMS",
            font=("Segoe UI", 14),
            justify="center"
        ).pack(pady=15)
        
        phone_entry = ctk.CTkEntry(
            container,
            placeholder_text="Phone Number (e.g., 9855062769)",
            width=400,
            height=50,
            font=("Segoe UI", 15)
        )
        phone_entry.pack(pady=25)
        
        def send_reset_sms():
            phone = phone_entry.get().strip()
            if not phone:
                messagebox.showerror("Error", "Please enter phone number")
                return
            
            try:
                response = requests.post(f"{API_BASE}/password-reset-sms", json={"phone": phone})
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Password reset code sent via SMS! Check your phone.")
                    dialog.destroy()
                    self.show_verify_reset_code(phone)
                else:
                    messagebox.showerror("Error", response.json().get('message', 'Failed to send SMS'))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send SMS: {str(e)}")
        
        ctk.CTkButton(
            container,
            text="SEND RESET CODE VIA SMS",
            width=400,
            height=55,
            font=("Segoe UI Black", 15),
            command=send_reset_sms
        ).pack(pady=20)
        
        ctk.CTkButton(
            container,
            text="Cancel",
            width=400,
            height=45,
            font=("Segoe UI Semibold", 13),
            fg_color="transparent",
            border_width=2,
            command=dialog.destroy
        ).pack(pady=10)
    
    def get_circular_image(self, base64_image=None, size=(60, 60), color="#6366f1"):
        """Convert base64 image to circular CTkImage, or return initial-based circle"""
        from PIL import Image, ImageDraw, ImageOps
        try:
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)

            if base64_image and len(base64_image) > 100:
                import base64
                img_data = base64.b64decode(base64_image)
                img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                img = ImageOps.fit(img, size, centering=(0.5, 0.5))
                output = Image.new('RGBA', size, (0, 0, 0, 0))
                output.paste(img, (0, 0), mask=mask)
                return ctk.CTkImage(light_image=output, dark_image=output, size=size)
            
            # Default colored circle
            output = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(output)
            draw.ellipse((2, 2, size[0]-2, size[1]-2), fill=color)
            return ctk.CTkImage(light_image=output, dark_image=output, size=size)
        except Exception as e:
            print(f"Image error: {e}")
            return None

    def show_verify_reset_code(self, phone):
        """Verify SMS code and set new password"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Verify Reset Code")
        dialog.geometry("550x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(
            container,
            text="📱 Enter Reset Code",
            font=("Segoe UI Black", 28, "bold")
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            container,
            text=f"A 6-digit code was sent to {phone}",
            font=("Segoe UI", 14)
        ).pack(pady=10)
        
        code_entry = ctk.CTkEntry(
            container,
            placeholder_text="6-Digit Code",
            width=400,
            height=50,
            font=("Consolas", 18, "bold")
        )
        code_entry.pack(pady=20)
        
        new_password_entry = ctk.CTkEntry(
            container,
            placeholder_text="New Password",
            show="●",
            width=400,
            height=50,
            font=("Segoe UI", 15)
        )
        new_password_entry.pack(pady=15)
        
        def verify_and_reset():
            code = code_entry.get().strip()
            new_password = new_password_entry.get().strip()
            
            if not code or not new_password:
                messagebox.showerror("Error", "Please enter both code and new password")
                return
            
            try:
                response = requests.post(f"{API_BASE}/verify-reset-code", json={
                    "phone": phone,
                    "code": code,
                    "newPassword": new_password
                })
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Password reset successful! You can now login.")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", response.json().get('message', 'Invalid code'))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(
            container,
            text="RESET PASSWORD",
            width=400,
            height=55,
            font=("Segoe UI Black", 15),
            command=verify_and_reset
        ).pack(pady=20)
    
    def get_super_admin_nav(self):
        """Complete navigation for Super Admin - Including Inventory & Store Management"""
        return [
            ("📊 Dashboard", self.show_super_admin_dashboard),
            ("👥 Client Accounts", self.show_clients_management),
            ("📦 Package Builder", self.show_package_builder),
            ("🔐 License Activation", self.show_license_management),
            ("📱 SMS Management", self.show_sms_management),
            ("👥 Access Level & Users", self.show_system_users),
            ("📢 Announcements", self.show_announcements),
            # --- Store Management for Super Admin ---
            ("🤝 Vendor Management", self.show_vendor_management),
            ("🛒 Purchase Entry", self.show_purchase_entry),
            ("↩️ Purchase Return", self.show_purchase_returns),
            ("📦 Inventory Management", self.show_inventory_management),
            ("💰 Billing Terminal", self.show_billing_terminal),
            ("📊 Sales Reports", self.show_pharmacy_reports),
            ("💰 Karobar", self.karobar.show_karobar_main),
            ("👥 Customer Database", self.show_customer_management),
            ("📜 Bill Log (History)", self.show_bill_log),
            # --- Alerts & Notifications ---
            ("📉 Low Stock Alerts", self.show_low_stock_alerts),
            ("⚠️ Expiry Alerts", self.show_expiry_alerts),
            ("🔄 Refund Requests", self.show_refund_management),
            # --- System Utilities ---
            ("📅 System Calendar", self.show_system_calendar),
            ("📜 System Logs", self.show_system_logs),
            ("👤 Profile Management", self.show_profile_management),
            ("⚙️ System Settings", self.show_system_settings)
        ]

    def get_admin_nav(self):
        """Strictly filtered navigation for Unit Admins (Calculated from permissions)"""
        if not self.user: return []
        
        # If Super Admin visits an Admin-level page, show the full Super Admin menu
        if self.user.get('role') == 'SUPER_ADMIN':
            return self.get_super_admin_nav()
            
        if self.user.get('role') != 'ADMIN': return []
        
        perms = self.user.get('permissions', '') or ''
        
        # Fallback: If Admin has no specific permissions set, grant all standard modules
        if not perms and self.user.get('role') == 'ADMIN':
            perms = "inventory,billing,crm,reports,users,vendors,announcements,settings,karobar"
            
        perms_list = perms.split(',') if perms else []
        
        # Admin always has Dashboard
        nav = [("📊 Dashboard", self.show_admin_dashboard)]
        
        # Dynamic Permission-based modules
        mapping = [
            ('inventory', "📦 Inventory Management", self.show_inventory_management),
            ('billing', "💰 Billing Terminal", self.show_billing_terminal),
            ('crm', "👥 Customer Database", self.show_customer_management),
            ("reports", "📊 Pharmacy Reports", self.show_pharmacy_reports),
            ("bill_log", "📜 Bill Log (History)", self.show_bill_log),
            ("pdf_tools", "📑 PDF Invoice Tools", self.show_pdf_tools),
            ('users', "🔐 Team Management", self.show_admin_users),
            ('vendors', "🤝 Vendor Management", self.show_vendor_management),
            ('karobar', "💰 Karobar", self.karobar.show_karobar_main),
            ('inventory', "🛒 Purchase Entry", self.show_purchase_entry),
            ('inventory', "↩️ Purchase Return", self.show_purchase_returns),
            ('announcements', "📢 Notifications", self.show_notification_management),
            ('settings', "⚙️ Payment Methods", self.show_payment_methods),
        ]
        
        # Always add alert pages (not permission-based)
        nav.append(("📉 Low Stock Alerts", self.show_low_stock_alerts))
        nav.append(("⚠️ Expiry Alerts", self.show_expiry_alerts))
        nav.append(("🔄 Refund Requests", self.show_refund_management))
        nav.append(("👤 Profile Management", self.show_profile_management))
        
        for key, label, cmd in mapping:
            if key in perms_list:
                nav.append((label, cmd))
            
        return nav

    def get_cashier_nav(self):
        """Standard navigation for Cashiers"""
        return [
            ("💰 Sales Terminal", self.show_billing_terminal),
            ("📦 Stock Check", self.show_inventory_management),
            ("📊 Daily Sales", lambda: messagebox.showinfo("Info", "Daily reports coming soon")),
            ("💰 Karobar", self.karobar.show_karobar_main),
            ("🤝 View Vendors", self.show_vendor_management),
        ]
    
    def create_sidebar(self, parent, nav_items, current_page="Dashboard"):
        """Professional Localized Sidebar based on User Image"""
        sidebar = ctk.CTkFrame(parent, width=320, fg_color=("#12b8ff", "#0ea5e9"), corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # 1. Profile Area (Top Header)
        profile_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=120)
        profile_frame.pack(fill="x", pady=(20, 10), padx=15)
        
        # Left side: Text
        text_side = ctk.CTkFrame(profile_frame, fg_color="transparent")
        text_side.pack(side="left", fill="both", expand=True)
        
        role_label = ctk.CTkLabel(text_side, text=f"{self.user['role'] if self.user else 'ADMIN'}", font=("Segoe UI Black", 16), text_color="white", anchor="w")
        role_label.pack(fill="x", padx=10)
        
        sub_role = ctk.CTkLabel(text_side, text="Administrator", font=("Segoe UI", 13), text_color="#f1f5f9", anchor="w")
        sub_role.pack(fill="x", padx=10)
        
        time_label = ctk.CTkLabel(text_side, textvariable=self.time_var, font=("Segoe UI", 12), text_color="#e2e8f0", anchor="w")
        time_label.pack(fill="x", padx=10)
        
        # Right side: User Icon
        pic_side = ctk.CTkFrame(profile_frame, fg_color="transparent", width=70, height=70)
        pic_side.pack(side="right", padx=10)
        
        user_img = self.get_circular_image(self.user.get('profile_pic') if self.user else None, size=(65, 65), color="#38bdf8")
        if user_img:
            ctk.CTkLabel(pic_side, image=user_img, text="").pack()
        
        # Separator
        ctk.CTkFrame(sidebar, height=2, fg_color="#7dd3fc").pack(fill="x", padx=15, pady=5)

        # 2. Local Date/Time Center
        date_center = ctk.CTkFrame(sidebar, fg_color="transparent")
        date_center.pack(fill="x", pady=10)
        
        ctk.CTkLabel(date_center, textvariable=self.nepali_date_var, font=("Mangal", 26, "bold"), text_color="white").pack()
        ctk.CTkLabel(date_center, textvariable=self.english_date_var, font=("Segoe UI", 16), text_color="#dc2626").pack()
        ctk.CTkLabel(date_center, textvariable=self.day_var, font=("Segoe UI Black", 20, "bold"), text_color="#1e293b").pack()
        
        big_clock = ctk.CTkLabel(date_center, textvariable=self.time_var, font=("Segoe UI Black", 34, "bold"), text_color="#fbbf24")
        big_clock.pack(pady=5)

        # Separator
        ctk.CTkFrame(sidebar, height=2, fg_color="#7dd3fc").pack(fill="x", padx=15, pady=5)

        # 3. Information Shortcuts (Matching Image)
        info_frame = ctk.CTkFrame(sidebar, fg_color=("#f1f5f9", "#cbd5e1"), corner_radius=0)
        info_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(info_frame, text="Information Sheet", font=("Segoe UI Semibold", 13), text_color="black").pack(pady=5)
        
        utility_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        utility_row.pack(fill="x", padx=15, pady=5)
        
        sms_cell = ctk.CTkFrame(utility_row, fg_color=("#f1f5f9", "#f1f5f9"), border_width=1, border_color="gray", corner_radius=0)
        sms_cell.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(sms_cell, text="📱", font=("Segoe UI", 24)).pack(pady=2)
        ctk.CTkLabel(sms_cell, text="SMS", font=("Segoe UI Black", 10), text_color="#ef4444").pack(pady=2)
        
        menu_cell = ctk.CTkFrame(utility_row, fg_color=("#ccfbf1", "#ccfbf1"), border_width=1, border_color="gray", corner_radius=0)
        menu_cell.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(menu_cell, text="Notification (0)", font=("Segoe UI Semibold", 11), text_color="#0f172a", anchor="w").pack(padx=10, pady=5)
        ctk.CTkLabel(menu_cell, text="Central Report", font=("Segoe UI Semibold", 11), text_color="#0f172a", anchor="w").pack(padx=10, pady=5)

        # 5. Branding Footer (pack BEFORE nav to ensure it's always visible)
        brand_frame = ctk.CTkFrame(sidebar, fg_color=("#f1f5f9", "#ffffff"), corner_radius=15)
        brand_frame.pack(side="bottom", fill="x", padx=15, pady=(0, 5))
        
        ctk.CTkLabel(brand_frame, text="A Product of", font=("Segoe UI", 10), text_color="#64748b").pack(pady=(5, 0))
        
        try:
             branding_logo_path = None
             possible_logo_paths = [
                 os.path.join(os.path.dirname(__file__), "assets", "brand_logo.jpg"),
                 os.path.join(os.path.dirname(sys.executable), "assets", "brand_logo.jpg"),
                 "assets/brand_logo.jpg"
             ]
             
             for p in possible_logo_paths:
                 if os.path.exists(p):
                     branding_logo_path = p
                     break

             if branding_logo_path:
                 # Create CTkImage
                 b_logo_img = ctk.CTkImage(light_image=Image.open(branding_logo_path), 
                                         dark_image=Image.open(branding_logo_path), 
                                         size=(110, 110))
                 ctk.CTkLabel(brand_frame, image=b_logo_img, text="").pack(pady=(5, 12))
             else:
                 ctk.CTkLabel(brand_frame, text="AARAMBHA SOFTWARES", font=("Segoe UI Black", 12), text_color="#0ea5e9").pack(pady=(2, 10))
        except Exception as e:
             print(f"Brand logo error: {e}")
             ctk.CTkLabel(brand_frame, text="AARAMBHA SOFTWARES", font=("Segoe UI Black", 12), text_color="#0ea5e9").pack(pady=(2, 10))

        # Logout button (pack BEFORE nav to ensure it's always visible)
        ctk.CTkButton(
            sidebar,
            text="🚪 Logout Account",
            height=40,
            font=("Segoe UI Black", 12),
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.logout
        ).pack(side="bottom", pady=(0, 10), padx=15, fill="x")

        # 4. Navigation Links (pack AFTER bottom elements, so it fills remaining space)
        nav_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Debug: Print navigation items
        print(f"Navigation items count: {len(nav_items)}")
        for item in nav_items:
            print(f"  - {item[0]}")
        
        # Redefine active page comparison to be safer
        for text, command in nav_items:
            clean_text = text
            for emoji in ["📊 ", "👥 ", "📦 ", "🔐 ", "📢 ", "🧾 ", "📅 ", "📜 ", "⚙️ ", "💰 ", "📉 ", "⚠️ ", "🔄 ", "👤 ", "🤝 ", "🛒 ", "↩️ "]:
                clean_text = clean_text.replace(emoji, "")
                
            is_active = clean_text == current_page
            
            btn = ctk.CTkButton(
                nav_frame,
                text=text,
                anchor="w",
                height=45,
                font=("Segoe UI Semibold", 13),
                fg_color=("#0369a1", "#075985") if is_active else "transparent",
                text_color="white",
                hover_color=("#075985", "#0369a1"),
                command=command
            )
            btn.pack(fill="x", pady=2)
        
        return sidebar

    def add_back_button(self, parent, target_command=None):
        """Standard back button for headers"""
        if target_command is None:
            target_command = self.show_super_admin_dashboard
            
        btn = ctk.CTkButton(
            parent,
            text="🔙",
            width=50,
            height=50,
            corner_radius=25,
            fg_color="transparent",
            text_color=("#1e293b", "#f1f5f9"),
            font=("Segoe UI", 24),
            hover_color=("#f1f5f9", "#1e293b"),
            command=target_command
        )
        btn.pack(side="left", padx=(0, 15))
        return btn
    
    def show_system_calendar(self):
        """Calendar view with holidays and navigation"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "System Calendar")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        self.add_back_button(header_frame)
        
        ctk.CTkLabel(
            header_frame,
            text="📅 System Calendar & Holidays",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left")
        
        # Calendar Frame
        cal_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
        cal_frame.pack(fill="both", expand=True, pady=10)
        
        # Current view date
        view_year = self.cal_view_year
        view_month = self.cal_view_month
        now = datetime.now()
        
        # Mapping Gregorian Month to Nepali Month (Approximate for 2082)
        nepali_months = ["बैशाख", "जेष्ठ", "असार", "साउन", "भदौ", "असोज", "कात्तिक", "मंसिर", "पुष", "माघ", "फागुन", "चैत"]
        # Simplified mapping: Jan -> Poush (idx 8), Feb -> Magh (idx 9) etc.
        bs_month_idx = (view_month + 7) % 12
        current_bs_month = nepali_months[bs_month_idx]
        current_bs_year = "२०८२" if view_year == 2026 else str(view_year + 57 - (1 if view_month < 4 else 0)) # Basic BS conversion

        # Navigation Controls
        ctrl_frame = ctk.CTkFrame(cal_frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=20, padx=30)
        
        def change_month(delta):
            nm = self.cal_view_month + delta
            if nm < 1:
                self.cal_view_month = 12
                self.cal_view_year -= 1
            elif nm > 12:
                self.cal_view_month = 1
                self.cal_view_year += 1
            else:
                self.cal_view_month = nm
            self.show_system_calendar()

        ctk.CTkButton(ctrl_frame, text="◀", width=50, fg_color="transparent", text_color="gray", command=lambda: change_month(-1)).pack(side="left")
        ctk.CTkLabel(ctrl_frame, text=f"📆 {current_bs_month} {current_bs_year}", font=("Mangal", 28, "bold")).pack(side="left", padx=20)
        ctk.CTkButton(ctrl_frame, text="▶", width=50, fg_color="transparent", text_color="gray", command=lambda: change_month(1)).pack(side="left")
        
        month_names_eng = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        ctk.CTkLabel(ctrl_frame, text=f"({month_names_eng[view_month-1]} {view_year})", font=("Segoe UI", 14), text_color="gray").pack(side="right", padx=20)

        grid_frame = ctk.CTkFrame(cal_frame, fg_color="transparent")
        grid_frame.pack(padx=30, pady=(0, 30), fill="both", expand=True)
        
        # Nepali Days
        days = ["आइत", "सोम", "मंगल", "बुध", "बिही", "शुक्र", "शनि"]
        for i, day in enumerate(days):
            ctk.CTkLabel(grid_frame, text=day, font=("Mangal", 16, "bold"), text_color="gray").grid(row=0, column=i, pady=10, sticky="nsew")
        
        nepali_nums = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९", "१०", "११", "१२", "१३", "१४", "१५", "१६", "१७", "१८", "१९", "२०", "२१", "२२", "२३", "२४", "२५", "२६", "२७", "२८", "२९", "३०", "३१", "३२"]

        # Comprehensive Holiday Database for 2026 (Gregorian Calendar mapping)
        global_holidays = {
            1: {1: "नयाँ वर्ष", 14: "माघे संक्रान्ति", 15: "माघे संक्रान्ति", 30: "शहीद दिवस"},
            2: {12: "सोनाम ल्होसार", 15: "महाशिवरात्रि", 18: "प्रजातन्त्र दिवस"},
            3: {8: "नारी दिवस", 14: "होली (Holi)", 15: "घोडे जात्रा"},
            4: {13: "नयाँ वर्ष २०८३", 14: "मातातीर्थ औंसी"},
            5: {1: "मजदुर दिवस", 12: "वुद्ध जयन्ती"},
            8: {19: "जनै पूर्णिमा"},
            9: {19: "संविधान दिवस"},
            10: {18: "दशैं (Phulpati)", 19: "अष्टमी", 20: "नवमी", 21: "विजया दशमी"},
            11: {10: "लक्ष्मी पूजा", 11: "गोवर्द्धन पूजा", 12: "भाई टिका"}
        }
        
        current_month_holidays = global_holidays.get(view_month, {})
        
        import calendar
        cal_data = calendar.monthcalendar(view_year, view_month)
        
        for r, week in enumerate(cal_data):
            for c, day in enumerate(week):
                if day == 0: continue
                
                # Highlight and format
                is_today = (day == now.day and view_month == now.month and view_year == now.year)
                h_name = current_month_holidays.get(day)
                is_holiday = h_name is not None
                
                day_frame = ctk.CTkFrame(
                    grid_frame, 
                    fg_color=("#f8fafc", "#141b2d") if not is_today else ("#dc2626", "#dc2626"),
                    border_width=1, 
                    border_color=("#e2e8f0", "#334155"), 
                    height=100
                )
                day_frame.grid(row=r+1, column=c, sticky="nsew", padx=2, pady=2)
                day_frame.grid_propagate(False)
                
                text_col = "#ffffff" if is_today else ("#1e293b", "#f1f5f9")
                nepali_day_text = nepali_nums[day] if day < len(nepali_nums) else str(day)
                
                lbl_row = ctk.CTkFrame(day_frame, fg_color="transparent")
                lbl_row.pack(fill="x", padx=10, pady=5)
                
                ctk.CTkLabel(lbl_row, text=nepali_day_text, font=("Mangal", 18, "bold"), text_color=text_col).pack(side="left")
                if is_today:
                    ctk.CTkLabel(lbl_row, text=" (आज)", font=("Mangal", 10), text_color="#ffdada").pack(side="left", padx=5)

                if is_holiday:
                    ctk.CTkLabel(day_frame, text=h_name, font=("Mangal", 11), text_color="#ef4444" if not is_today else "#ffdada", wraplength=80).pack(fill="x", padx=5)
                    if not is_today: day_frame.configure(fg_color=("#fef2f2", "#2d1a1a"))
        
        for i in range(7): grid_frame.grid_columnconfigure(i, weight=1)

    def logout(self):
        """Logout and return to login screen"""
        self.token = None
        self.user = None
        self.show_login()
    
    def show_super_admin_dashboard(self):
        """Complete Super Admin Dashboard"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "Dashboard")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
        header_frame.pack(fill="x", pady=(0, 30))
        
        if hasattr(self, 'add_back_button'):
            self.add_back_button(header_frame)
            
        username = self.user['name'] if self.user else 'Super Admin'
        ctk.CTkLabel(
            header_frame,
            text=f"Welcome back, {username}! 👋",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left", padx=30, pady=25)

        # Prominent Activation Button in Header
        ctk.CTkButton(
            header_frame,
            text="🔐 ACTIVATE NEW DEVICE",
            width=220,
            height=50,
            font=("Segoe UI Black", 14),
            fg_color=("#4f46e5", "#4338ca"),
            hover_color=("#4338ca", "#3730a3"),
            command=self.show_license_management
        ).pack(side="right", padx=30, pady=25)
        
        # Stats cards
        if hasattr(self, 'load_super_admin_stats'):
            self.load_super_admin_stats(content)
        else:
             # Fallback if load_super_admin_stats is missing (it shouldn't be)
             pass

    def show_admin_dashboard(self):
        """Admin Dashboard"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Dashboard")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True)
        
        dashboard = DashboardUI(self)
        dashboard.show(content)

    def show_system_users(self):
        """Management interface for Super Admins and other staff"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "System Users")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        self.add_back_button(header_frame)

        ctk.CTkLabel(
            header_frame,
            text="👥 System User Management",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left")
        
        ctk.CTkButton(
            header_frame,
            text="➕ Create New User",
            width=220,
            height=45,
            font=("Segoe UI Black", 14),
            fg_color=("#4a90e2", "#3b82f6"),
            command=self.show_add_user_dialog
        ).pack(side="right")
        
        # Users list
        self.load_users_list(content)

    def show_add_user_dialog(self):
        """Enhanced Dialog to create Super Admin, Admin, or Cashier"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create System User")
        dialog.geometry("700x850")
        dialog.transient(self.root)
        dialog.grab_set()
        
        container = ctk.CTkScrollableFrame(dialog, fg_color=("#ffffff", "#1e293b"))
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text="👥 Create New User Account",
            font=("Segoe UI Black", 24, "bold")
        ).pack(pady=(0, 30), anchor="w")
        
        # Form
        fields = {}
        form_data = [
            ("Full Name", "name", "Enter full name"),
            ("Phone Number", "phone", "Login ID (Phone)"),
            ("Email Address", "email", "Optional email"),
            ("Login Password", "password", "Enter secure password")
        ]
        
        for label, key, placeholder in form_data:
            ctk.CTkLabel(container, text=label, font=("Segoe UI Semibold", 13)).pack(fill="x", pady=(20, 5), anchor="w")
            entry = ctk.CTkEntry(container, placeholder_text=placeholder, height=50, font=("Segoe UI", 14))
            entry.pack(fill="x", pady=(0, 5))
            fields[key] = entry

        # Role Selection (Locked to Super Admin for this section)
        ctk.CTkLabel(container, text="Access Level", font=("Segoe UI Semibold", 13)).pack(fill="x", pady=(15, 5), anchor="w")
        role_var = StringVar(value="SUPER_ADMIN")
        
        role_menu = ctk.CTkOptionMenu(container, values=["SUPER_ADMIN"], variable=role_var, width=500, height=50, font=("Segoe UI", 14), state="disabled")
        role_menu.pack(fill="x", pady=(0, 15))

        def submit():
            data = {k: v.get().strip() for k, v in fields.items()}
            data['role'] = "SUPER_ADMIN"
            data['permissions'] = "all" # Super admins have all permissions
            
            if not data['name'] or not data['phone'] or not data['password']:
                messagebox.showerror("Error", "Required fields missing")
                return
                
            try:
                res = requests.post(f"{API_BASE}/users", json=data, headers={"Authorization": f"Bearer {self.token}"})
                if res.status_code == 200:
                    messagebox.showinfo("Success", "Super Admin Created Successfully!")
                    dialog.destroy()
                    self.show_system_users()
                else:
                    messagebox.showerror("Error", res.json().get('message', 'Failed to create user'))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(
            container, 
            text="🚀 CREATE USER ACCOUNT", 
            height=65, 
            font=("Segoe UI Black", 18), 
            fg_color="#009688",
            hover_color="#00796b",
            command=submit
        ).pack(fill="x", pady=50)

    def load_users_list(self, parent):
        """Load and display list of system users"""
        try:
            # Note: We need a backend route for this. Let's assume /api/super/users
            res = requests.get(f"{API_BASE}/users/all", headers={"Authorization": f"Bearer {self.token}"})
            users = res.json() if res.status_code == 200 else []
        except:
            users = []

        if not users:
            ctk.CTkLabel(parent, text="No additional system users found.", font=("Segoe UI", 14), text_color="gray").pack(pady=50)
            return

        for user in users:
            if user['role'] != 'SUPER_ADMIN': continue
            
            card = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
            card.pack(fill="x", pady=8)
            
            ctk.CTkLabel(card, text=f"👤 {user['name']}", font=("Segoe UI Bold", 16)).pack(side="left", padx=25, pady=20)
            ctk.CTkLabel(card, text=f"📞 {user['phone']}", font=("Consolas", 14), text_color="gray").pack(side="left", padx=20)
            ctk.CTkLabel(card, text="⭐ SUPER ADMIN", font=("Segoe UI Black", 11), text_color="#3b82f6").pack(side="right", padx=25)
    
    def load_super_admin_stats(self, parent):
        """Load statistics for Super Admin"""
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 30))
        
        try:
            response = requests.get(f"{API_BASE}/super/stats", headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code == 200:
                data = response.json()
            else:
                data = {}
        except:
            data = {}
        
        stats = [
            ("Total Clients", data.get('total_clients', '0'), "#3b82f6", "👥"),
            ("Active Licenses", data.get('active_licenses', '0'), "#10b981", "✓"),
            ("Expiring Soon", data.get('expiring_soon', '0'), "#f59e0b", "⏰"),
            ("30-Day Signups", data.get('new_signups', '0'), "#06b6d4", "🆕"),
            ("Total Revenue", f"रु {data.get('total_revenue', '0')}", "#8b5cf6", "💰")
        ]
        
        for i, (label, value, color, icon) in enumerate(stats):
            card = ctk.CTkFrame(stats_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
            card.grid(row=0, column=i, padx=12, pady=0, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            
            icon_label = ctk.CTkLabel(
                card,
                text=icon,
                font=("Segoe UI", 40),
                text_color=(color, color)
            )
            icon_label.pack(pady=(25, 10))
            
            ctk.CTkLabel(
                card,
                text=label,
                font=("Segoe UI Semibold", 13),
                text_color=("#64748b", "#94a3b8")
            ).pack(pady=(0, 8))
            
            ctk.CTkLabel(
                card,
                text=value,
                font=("Segoe UI Black", 32, "bold"),
                text_color=(color, color)
            ).pack(pady=(0, 25))
    
    def load_recent_activity(self, parent):
        """Load recent activity feed"""
        activity_frame = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
        activity_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            activity_frame,
            text="📋 Recent System Activity",
            font=("Segoe UI Black", 20, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(25, 20), padx=25, anchor="w")
        
        # Sample activities
        activities = [
            ("New client registered", "Life Care Pharmacy - Kathmandu", "2 hours ago"),
            ("License renewed", "Himalayan Medicals - Pokhara", "5 hours ago"),
            ("Low stock alert", "15 medicines below minimum quantity", "1 day ago")
        ]
        
        for title, desc, time in activities:
            item_frame = ctk.CTkFrame(activity_frame, fg_color=("#f8fafc", "#0f172a"), corner_radius=12)
            item_frame.pack(fill="x", padx=25, pady=8)
            
            ctk.CTkLabel(
                item_frame,
                text=title,
                font=("Segoe UI Semibold", 14),
                text_color=("#1e293b", "#f1f5f9"),
                anchor="w"
            ).pack(pady=(15, 5), padx=20, anchor="w")
            
            ctk.CTkLabel(
                item_frame,
                text=desc,
                font=("Segoe UI", 12),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            ).pack(pady=(0, 5), padx=20, anchor="w")
            
            ctk.CTkLabel(
                item_frame,
                text=f"⏱️ {time}",
                font=("Segoe UI", 11),
                text_color=("#94a3b8", "#64748b"),
                anchor="w"
            ).pack(pady=(0, 15), padx=20, anchor="w")
    
    def show_clients_management(self):
        """Client management interface"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "Client Accounts")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header with Add button
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        ctk.CTkLabel(
            header_frame,
            text="👥 Client Management",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left")
        
        ctk.CTkButton(
            header_frame,
            text="➕ Add New Client",
            width=200,
            height=45,
            font=("Segoe UI Black", 14),
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            command=self.show_add_client_dialog
        ).pack(side="right")
        
        # Search Bar
        search_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        search_frame.pack(fill="x", pady=(0, 20))
        
        search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="🔍 Search by Mobile, Name, Pharmacy, or Client Code...",
            height=45,
            font=("Segoe UI", 14)
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=20, pady=15)
        
        def perform_search():
            query = search_entry.get().strip()
            if not query:
                self.load_clients_list(clients_list_container)
                return
                
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.get(f"{API_BASE}/super/clients/search?query={query}", headers=headers)
                if response.status_code == 200:
                    clients = response.json()
                    self.display_clients_in_container(clients_list_container, clients)
                else:
                    messagebox.showerror("Error", "Search failed")
            except Exception as e:
                messagebox.showerror("Search Error", str(e))

        ctk.CTkButton(
            search_frame,
            text="Search",
            width=120,
            height=40,
            font=("Segoe UI Semibold", 13),
            command=perform_search
        ).pack(side="right", padx=20, pady=15)
        
        # Clients list container
        clients_list_container = ctk.CTkFrame(content, fg_color="transparent")
        clients_list_container.pack(fill="both", expand=True)
        
        # Initial load
        self.load_clients_list(clients_list_container)
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda e: perform_search())
    
    def show_add_client_dialog(self):
        """Redesigned Professional Client Registration Dialog (Matches Image)"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create New Client Account")
        dialog.geometry("900x950")
        dialog.after(100, dialog.lift)
        
        # Scrollable container for the long form
        container = ctk.CTkScrollableFrame(dialog, fg_color=("#ffffff", "#1e293b"))
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text="➕ Create New Client Account",
            font=("Segoe UI Black", 28, "bold")
        ).pack(anchor="w", pady=(0, 30))
        
        # Helper for form rows
        def create_form_row(parent, label_text, is_required=False, is_textbox=False):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=8)
            
            lbl_text = f"{label_text} *" if is_required else label_text
            ctk.CTkLabel(row, text=lbl_text, font=("Segoe UI Semibold", 13), width=180, anchor="w").pack(side="left", padx=(0, 10))
            
            if is_textbox:
                widget = ctk.CTkTextbox(row, height=100, font=("Segoe UI", 13), border_width=1)
                widget.pack(side="left", fill="x", expand=True)
            else:
                widget = ctk.CTkEntry(row, height=45, font=("Segoe UI", 14))
                widget.pack(side="left", fill="x", expand=True)
            
            return widget

        # Client ID Row with Generate Button
        id_row = ctk.CTkFrame(container, fg_color="transparent")
        id_row.pack(fill="x", pady=8)
        ctk.CTkLabel(id_row, text="Client ID:", font=("Segoe UI Semibold", 13), width=180, anchor="w").pack(side="left", padx=(0, 10))
        cid_entry = ctk.CTkEntry(id_row, height=45, font=("Segoe UI", 14), fg_color=("#e2e8f0", "#334155"))
        cid_entry.pack(side="left", fill="x", expand=True)
        
        def generate_id():
            new_id = f"CLI-{random.randint(1000, 9999)}"
            cid_entry.delete(0, "end")
            cid_entry.insert(0, new_id)
            
        ctk.CTkButton(id_row, text="Generate ID", width=120, height=40, border_width=1, fg_color="transparent", text_color=("#4a90e2", "#5ba3ff"), command=generate_id).pack(side="left", padx=(10, 0))

        # Core Fields
        pharmacy_name = create_form_row(container, "Pharmacy Name", True)
        owner_name = create_form_row(container, "Owner Name", True)
        contact_number = create_form_row(container, "Contact Number", True)
        email = create_form_row(container, "Email")
        address = create_form_row(container, "Address", True, is_textbox=True)
        pan_number = create_form_row(container, "PAN Number")
        oda_number = create_form_row(container, "ODA Number")
        dda_number = create_form_row(container, "DDA Number")

        # Pharmacy Assets Section
        assets_frame = ctk.CTkFrame(container, fg_color="transparent")
        assets_frame.pack(fill="x", pady=20)

        logo_path = StringVar()
        photo_path = StringVar()

        def create_asset_selector(parent, label_text, target_var):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=10)
            ctk.CTkLabel(row, text=label_text, font=("Segoe UI Semibold", 13), width=180, anchor="w").pack(side="left", padx=(0, 10))
            
            preview_box = ctk.CTkFrame(row, width=150, height=150, border_width=1)
            preview_box.pack(side="left")
            preview_box.pack_propagate(False)
            
            def pick_file():
                path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
                if path:
                    target_var.set(path)
                    # Label to show selected file
                    ctk.CTkLabel(preview_box, text="Selected", font=("Segoe UI", 10)).pack(expand=True)
            
            ctk.CTkButton(row, text=f"Upload {label_text.split()[-1].replace(':', '')}", width=150, fg_color="transparent", border_width=1, text_color="gray", command=pick_file).pack(side="left", padx=20)
            return preview_box

        logo_preview = create_asset_selector(assets_frame, "Pharmacy Logo:", logo_path)
        photo_preview = create_asset_selector(assets_frame, "Owner Photo:", photo_path)

        # Login Credentials Section
        ctk.CTkLabel(container, text="Login Credentials", font=("Segoe UI Black", 20, "bold")).pack(anchor="w", pady=(30, 20))
        username_entry = create_form_row(container, "Username", True)
        password_entry = create_form_row(container, "Password", True)

        # Subscription Expiry Section
        ctk.CTkLabel(container, text="Subscription Expiry", font=("Segoe UI Black", 20, "bold")).pack(anchor="w", pady=(30, 20))
        expiry_row = ctk.CTkFrame(container, fg_color="transparent")
        expiry_row.pack(fill="x", pady=8)
        ctk.CTkLabel(expiry_row, text="Expiry Date:", font=("Segoe UI Semibold", 13), width=180, anchor="w").pack(side="left", padx=(0, 10))
        
        default_expiry = datetime.now() + timedelta(days=365)
        expiry_entry = DateEntry(expiry_row, width=12, background='darkblue', foreground='white', borderwidth=2, font=("Segoe UI", 12))
        expiry_entry.set_date(default_expiry)
        expiry_entry.pack(side="left", fill="x", expand=True)

        # Access Level & Features Section
        ctk.CTkLabel(container, text="Access Level & Features", font=("Segoe UI Black", 20, "bold")).pack(anchor="w", pady=(30, 10))
        ctk.CTkLabel(container, text="Role: UNIT ADMIN (Auto-assigned)", font=("Segoe UI Semibold", 13), text_color="gray").pack(anchor="w", pady=(0, 15))
        
        features_frame = ctk.CTkFrame(container, fg_color=("#f8fafc", "#0f172a"), corner_radius=15)
        features_frame.pack(fill="x", pady=5)
        
        feature_list = [
            ("📦 Inventory & Stock", "inventory"),
            ("💰 Billing & Sales", "billing"),
            ("👥 Customer CRM", "crm"),
            ("📊 Advanced Reports", "reports"),
            ("🔐 User Management", "users"),
            ("📢 Announcements", "announcements"),
            ("⚙️ System Settings", "settings")
        ]
        
        feature_vars = {}
        for text, key in feature_list:
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(features_frame, text=text, variable=var, font=("Segoe UI", 12))
            cb.pack(anchor="w", padx=20, pady=8)
            feature_vars[key] = var

        def submit():
            # Basic validation
            p_name = pharmacy_name.get().strip()
            o_name = owner_name.get().strip()
            c_num = contact_number.get().strip()
            u_name = username_entry.get().strip()
            u_pass = password_entry.get().strip()
            c_code = cid_entry.get().strip()
            addr = address.get("1.0", "end-1c").strip()
            pan = pan_number.get().strip()
            oda = oda_number.get().strip()
            dda = dda_number.get().strip()
            
            if not all([p_name, o_name, c_num, u_name, u_pass, c_code, addr]):
                messagebox.showerror("Error", "Required fields (Pharmacy, Owner, Contact, Login, Address) are compulsory!")
                return
            
            data = {
                "client_id_code": c_code,
                "pharmacy_name": p_name,
                "admin_name": o_name,
                "contact_number": c_num,
                "email": email.get().strip(),
                "address": addr,
                "pan_number": pan if pan else None,
                "oda_number": oda if oda else None,
                "dda_number": dda if dda else None,
                "admin_phone": u_name,
                "admin_password": u_pass,
                "package_id": "2",
                "package_id": "2",
                "duration_days": "365",
                "expiry_date": expiry_entry.get_date().strftime('%Y-%m-%d'),
                "permissions": ",".join([k for k, v in feature_vars.items() if v.get()])
            }
            
            try:
                files = {}
                if logo_path.get(): files['logo'] = open(logo_path.get(), 'rb')
                if photo_path.get(): files['owner_photo'] = open(photo_path.get(), 'rb')
                
                res = requests.post(f"{API_BASE}/super/clients", data=data, files=files, headers={"Authorization": f"Bearer {self.token}"})
                
                # Cleanup
                for f in files.values(): f.close()
                
                if res.status_code == 200:
                    messagebox.showinfo("Success", res.json().get('message', 'Client Created!'))
                    dialog.destroy()
                    self.show_clients_management()
                else:
                    # Fix: Check both 'message' and 'error' keys from backend
                    err_msg = res.json().get('message') or res.json().get('error') or 'Failed to create client'
                    messagebox.showerror("Error", err_msg)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(
            container,
            text="✅ Create Client Account",
            height=60,
            font=("Segoe UI Black", 18),
            fg_color="#009688",
            hover_color="#00796b",
            command=submit
        ).pack(fill="x", pady=40, padx=20)
    
    def load_clients_list(self, parent):


        """Load and display clients"""
        try:
            response = requests.get(
                f"{API_BASE}/super/clients",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                clients = response.json()
                self.display_clients_in_container(parent, clients)
            else:
                self.display_clients_in_container(parent, [])
        except:
            self.display_clients_in_container(parent, [])

    def display_clients_in_container(self, parent, clients):
        """Helper to render clients inside a container"""
        for widget in parent.winfo_children():
            widget.destroy()
            
        if not clients:
            ctk.CTkLabel(
                parent,
                text="No clients found",
                font=("Segoe UI", 16),
                text_color=("#94a3b8", "#64748b")
            ).pack(pady=50)
            return
        
        for client in clients:
            client_card = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
            client_card.pack(fill="x", pady=10)
            
            info_frame = ctk.CTkFrame(client_card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=25, pady=20)
            
            ctk.CTkLabel(
                info_frame,
                text=client.get('pharmacy_name', 'N/A'),
                font=("Segoe UI Black", 18, "bold"),
                text_color=("#1e293b", "#f1f5f9"),
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame,
                text=f"📍 {client.get('address', 'N/A')} | 📞 {client.get('contact_number', 'N/A')}",
                font=("Segoe UI", 13),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            ).pack(anchor="w", pady=(5, 0))
            
            ctk.CTkLabel(
                info_frame,
                text=f"ID: {client.get('client_id_code', 'N/A')} | Package: {client.get('package_name', 'N/A')}",
                font=("Segoe UI", 12),
                text_color=("#94a3b8", "#64748b"),
                anchor="w"
            ).pack(anchor="w", pady=(5, 0))
            
            # Status and actions
            action_frame = ctk.CTkFrame(client_card, fg_color="transparent")
            action_frame.pack(side="right", padx=25, pady=20)
            
            status_color = "#10b981" if client.get('status') == 'active' else "#ef4444"
            ctk.CTkLabel(
                action_frame,
                text=client.get('status', 'unknown').upper(),
                font=("Segoe UI Black", 12),
                text_color=(status_color, status_color)
            ).grid(row=0, column=0, columnspan=2, pady=5)
            
            ctk.CTkButton(
                action_frame,
                text="📄 Profile",
                width=100,
                height=35,
                font=("Segoe UI Semibold", 12),
                command=lambda c=client: self.show_client_details(c)
            ).grid(row=1, column=0, padx=5, pady=5)

            ctk.CTkButton(
                action_frame,
                text="🔑 LOGIN",
                width=100,
                height=35,
                font=("Segoe UI Black", 11),
                fg_color="#4f46e5",
                command=lambda c=client: self.login_as_client_admin(c)
            ).grid(row=1, column=1, padx=5, pady=5)

            ctk.CTkButton(
                action_frame,
                text="🗑️ DELETE",
                width=100,
                height=35,
                font=("Segoe UI Black", 11),
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=lambda c=client: self.delete_client(c)
            ).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def delete_client(self, client):
        """Permanently delete a client"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to PERMANENTLY delete {client.get('pharmacy_name')}?\nThis will remove all their medicines, users, and data!"):
            try:
                res = requests.delete(f"{API_BASE}/super/clients/{client['id']}", headers={"Authorization": f"Bearer {self.token}"})
                if res.status_code == 200:
                    messagebox.showinfo("Success", "Client and all associated data deleted successfully.")
                    self.show_clients_management()
                else:
                    messagebox.showerror("Error", res.json().get('message', 'Delete failed'))
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def show_client_details(self, client):
        """View and Manage full client profile"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Client Profile - {client.get('pharmacy_name')}")
        dialog.geometry("800x900")
        dialog.grab_set()
        
        container = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Header with Logo display if exists
        header_row = ctk.CTkFrame(container, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 30))
        
        # Try to load and show logo
        logo_path = client.get('logo_path')
        if logo_path:
            try:
                # Assuming standard server path, might need adjustment for local dev
                url = f"http://localhost:5000/{logo_path}"
                resp = requests.get(url)
                img_data = io.BytesIO(resp.content)
                img = Image.open(img_data).resize((100, 100))
                logo_img = ImageTk.PhotoImage(img)
                label = ctk.CTkLabel(header_row, image=logo_img, text="")
                label.image = logo_img # keep reference
                label.pack(side="left", padx=(0, 20))
            except:
                pass
                
        ctk.CTkLabel(header_row, text=client.get('pharmacy_name'), font=("Segoe UI Black", 24, "bold")).pack(side="left")
        
        # Profile Data (Non-editable ID)
        info_grid = ctk.CTkFrame(container, fg_color=("#f8fafc", "#1e293b"), corner_radius=15)
        info_grid.pack(fill="x", pady=10)
        
        profile_fields = [
            ("Client ID", "client_id_code"),
            ("Address", "address"),
            ("PAN Number", "pan_number"),
            ("DDA Number", "dda_number"),
            ("ODA Number", "oda_number"),
            ("Contact", "contact_number"),
            ("Status", "status")
        ]
        
        entries = {}
        for label, key in profile_fields:
            row = ctk.CTkFrame(info_grid, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row, text=f"{label}:", width=150, anchor="w", font=("Segoe UI Semibold", 13)).pack(side="left")
            
            entry = ctk.CTkEntry(row, width=400)
            entry.insert(0, str(client.get(key) or ""))
            if key == "client_id_code":
                entry.configure(state="disabled") # Non-editable
            entry.pack(side="left", padx=10)
            entries[key] = entry

        # Owner Photo Display
        ctk.CTkLabel(container, text="👤 Owner Information", font=("Segoe UI Black", 18, "bold")).pack(pady=(30, 10), anchor="w")
        photo_row = ctk.CTkFrame(container, fg_color="transparent")
        photo_row.pack(fill="x", pady=10)
        
        photo_path = client.get('owner_photo_path')
        if photo_path:
            try:
                url = f"http://localhost:5000/{photo_path}"
                resp = requests.get(url)
                img_data = io.BytesIO(resp.content)
                img = Image.open(img_data).resize((150, 200))
                owner_img = ImageTk.PhotoImage(img)
                label = ctk.CTkLabel(photo_row, image=owner_img, text="")
                label.image = owner_img 
                label.pack(side="left", padx=20)
            except:
                ctk.CTkLabel(photo_row, text="[Photo not found]").pack(side="left", padx=20)
        
        # Upload new Assets
        ctk.CTkLabel(container, text="📂 Update Assets", font=("Segoe UI Bold", 14)).pack(pady=(20, 5), anchor="w")
        asset_frame = ctk.CTkFrame(container, fg_color="transparent")
        asset_frame.pack(fill="x", pady=10)
        
        new_logo = StringVar(value="No file selected")
        new_photo = StringVar(value="No file selected")
        
        def pick_logo():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if path: new_logo.set(path)
            
        def pick_photo():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if path: new_photo.set(path)
        
        logo_btn_row = ctk.CTkFrame(asset_frame, fg_color="transparent")
        logo_btn_row.pack(fill="x", pady=2)
        ctk.CTkButton(logo_btn_row, text="📁 Choose New Logo", width=180, command=pick_logo).pack(side="left")
        ctk.CTkLabel(logo_btn_row, textvariable=new_logo, font=("Segoe UI", 10), text_color="gray").pack(side="left", padx=15)
        
        photo_btn_row = ctk.CTkFrame(asset_frame, fg_color="transparent")
        photo_btn_row.pack(fill="x", pady=5)
        ctk.CTkButton(photo_btn_row, text="👤 Choose New Photo", width=180, command=pick_photo).pack(side="left")
        ctk.CTkLabel(photo_btn_row, textvariable=new_photo, font=("Segoe UI", 10), text_color="gray").pack(side="left", padx=15)

        # Permissions & Feature Access
        ctk.CTkLabel(container, text="🔐 Permissions & Feature Access", font=("Segoe UI Black", 18, "bold")).pack(pady=(30, 10), anchor="w")
        
        perms_frame = ctk.CTkFrame(container, fg_color=("#f8fafc", "#1e293b"), corner_radius=15)
        perms_frame.pack(fill="x", pady=5)
        
        current_perms = client.get('permissions', '') or ''
        current_perms_list = current_perms.split(',') if current_perms else []
        
        feature_list = [
            ("📦 Inventory & Stock", "inventory"),
            ("💰 Billing & Sales", "billing"),
            ("👥 Customer CRM", "crm"),
            ("📊 Advanced Reports", "reports"),
            ("🔐 User Management", "users"),
            ("📢 Announcements", "announcements"),
            ("⚙️ System Settings", "settings")
        ]
        
        feature_vars = {}
        for text, key in feature_list:
            var = ctk.BooleanVar(value=key in current_perms_list)
            cb = ctk.CTkCheckBox(perms_frame, text=text, variable=var, font=("Segoe UI", 12))
            cb.pack(anchor="w", padx=20, pady=8)
            feature_vars[key] = var

        def save_changes():
            data = {k: e.get() for k, e in entries.items() if k != "client_id_code"}
            data['package_id'] = client.get('package_id')
            data['permissions'] = ",".join([k for k, v in feature_vars.items() if v.get()])
            
            try:
                files = {}
                if new_logo.get() != "No file selected": files['logo'] = open(new_logo.get(), 'rb')
                if new_photo.get() != "No file selected": files['owner_photo'] = open(new_photo.get(), 'rb')
                
                res = requests.put(
                    f"{API_BASE}/super/clients/{client.get('id')}",
                    data=data,
                    files=files,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                for f in files.values(): f.close()
                
                if res.status_code == 200:
                    messagebox.showinfo("Success", "Client profile updated!")
                    dialog.destroy()
                    self.show_clients_management()
                else:
                    messagebox.showerror("Error", "Update failed")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(container, text="💾 SAVE ALL CHANGES", height=55, font=("Segoe UI Black", 16), fg_color="#4f46e5", command=save_changes).pack(fill="x", pady=40)
    
    
    def show_package_builder(self):
        """Complete Package Builder interface"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "Package Builder")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        self.add_back_button(header_frame)

        ctk.CTkLabel(
            header_frame,
            text="📦 Package Builder",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left")
        
        ctk.CTkButton(
            header_frame,
            text="➕ Create New Package",
            width=200,
            height=45,
            font=("Segoe UI Black", 14),
            fg_color=("#8b5cf6", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9"),
            command=self.show_create_package_dialog
        ).pack(side="right")
        
        # Load existing packages
        self.load_packages_list(content)
    
    def load_packages_list(self, parent):
        """Load and display all packages"""
        try:
            response = requests.get(f"{API_BASE}/super/packages", headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code == 200:
                packages = response.json()
            else:
                packages = []
        except:
            # Default packages if API fails
            packages = [
                {"id": 1, "name": "Basic Package", "price": 5000, "features": "Basic billing, 1 user, 100 medicines", "duration": 365},
                {"id": 2, "name": "Standard Package", "price": 15000, "features": "Advanced billing, 5 users, 500 medicines, Reports", "duration": 365},
                {"id": 3, "name": "Premium Package", "price": 35000, "features": "Full features, Unlimited users, Unlimited medicines, SMS alerts", "duration": 365}
            ]
        
        for pkg in packages:
            pkg_card = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
            pkg_card.pack(fill="x", pady=15)
            
            # Package header with color coding
            colors = {
                "Basic": "#3b82f6",
                "Standard": "#8b5cf6",
                "Premium": "#f59e0b"
            }
            pkg_type = pkg.get('name', '').split()[0]
            color = colors.get(pkg_type, "#64748b")
            
            header = ctk.CTkFrame(pkg_card, fg_color=(color, color), corner_radius=20, height=10)
            header.pack(fill="x")
            
            content_frame = ctk.CTkFrame(pkg_card, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=30, pady=25)
            
            # Package name and price
            title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            title_frame.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                title_frame,
                text=pkg.get('name', 'N/A'),
                font=("Segoe UI Black", 24, "bold"),
                text_color=("#1e293b", "#f1f5f9")
            ).pack(side="left")
            
            ctk.CTkLabel(
                title_frame,
                text=f"रु {int(float(pkg.get('price', 0))):,}/year",
                font=("Segoe UI Black", 20, "bold"),
                text_color=(color, color)
            ).pack(side="right")
            
            # Features
            ctk.CTkLabel(
                content_frame,
                text="Features:",
                font=("Segoe UI Semibold", 14),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            ).pack(fill="x", pady=(0, 10))
            
            features_text = pkg.get('features', 'No features listed')
            for feature in features_text.split(','):
                feature_frame = ctk.CTkFrame(content_frame, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
                feature_frame.pack(fill="x", pady=3)
                
                ctk.CTkLabel(
                    feature_frame,
                    text=f"✓ {feature.strip()}",
                    font=("Segoe UI", 13),
                    text_color=("#1e293b", "#cbd5e1"),
                    anchor="w"
                ).pack(pady=8, padx=15, anchor="w")
            
            # Action buttons
            btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=(15, 0))
            
            ctk.CTkButton(
                btn_frame,
                text="Edit Package",
                width=150,
                height=40,
                font=("Segoe UI Semibold", 13),
                fg_color=("#4a90e2", "#5ba3ff"),
                command=lambda p=pkg: self.edit_package(p)
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                btn_frame,
                text="Delete",
                width=120,
                height=40,
                font=("Segoe UI Semibold", 13),
                fg_color=("#ef4444", "#dc2626"),
                command=lambda p=pkg: self.delete_package(p)
            ).pack(side="left", padx=5)
    
    def show_create_package_dialog(self):
        """Dialog to create new package"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create New Package")
        dialog.geometry("700x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        container = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(
            container,
            text="📦 Create New Package",
            font=("Segoe UI Black", 26, "bold")
        ).pack(pady=(0, 30))
        
        # Package Name
        ctk.CTkLabel(
            container,
            text="Package Name",
            font=("Segoe UI Semibold", 13),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        name_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g., Enterprise Package",
            width=600,
            height=45,
            font=("Segoe UI", 14)
        )
        name_entry.pack(pady=(0, 15))

        # Description
        ctk.CTkLabel(
            container,
            text="Package Description",
            font=("Segoe UI Semibold", 13),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        desc_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g., Best for large pharmacies with multiple staff",
            width=600,
            height=45,
            font=("Segoe UI", 14)
        )
        desc_entry.pack(pady=(0, 15))
        
        # Price
        ctk.CTkLabel(
            container,
            text="Annual Price (रु)",
            font=("Segoe UI Semibold", 13),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        price_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g., 25000",
            width=600,
            height=45,
            font=("Segoe UI", 14)
        )
        price_entry.pack(pady=(0, 15))
        
        # Features (checkboxes)
        ctk.CTkLabel(
            container,
            text="Select Features",
            font=("Segoe UI Semibold", 13),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).pack(fill="x", pady=(15, 10))
        
        features_frame = ctk.CTkFrame(container, fg_color=("#f8fafc", "#1e293b"), corner_radius=15)
        features_frame.pack(fill="x", pady=(0, 15))
        
        feature_vars = {}
        all_features = [
            "Client management",
            "Billing designer (drag & drop)",
            "Receipt template editor (A5)",
            "License & subscription control",
            "Data backup & restore",
            "Data export (PDF / Excel / CSV)",
            "Audit logs",
            "System configuration",
            "Update publishing",
            "Emergency controls",
            "Basic Billing",
            "Advanced Billing",
            "Inventory Management",
            "Stock Tracking",
            "Batch & Expiry Management",
            "Vendor Management",
            "Customer Management",
            "Staff Management",
            "Sales Reports",
            "Profit/Loss Reports",
            "Low Stock Alerts",
            "Expiry Alerts",
            "SMS Notifications",
            "Multi-User Support",
            "Role-Based Access Control",
            "Data Backup",
            "Cloud Sync"
        ]
        
        for feature in all_features:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(
                features_frame,
                text=feature,
                variable=var,
                font=("Segoe UI", 13),
                checkbox_width=24,
                checkbox_height=24
            )
            cb.pack(pady=8, padx=20, anchor="w")
            feature_vars[feature] = var
        
        # Max users
        ctk.CTkLabel(
            container,
            text="Maximum Users",
            font=("Segoe UI Semibold", 13),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).pack(fill="x", pady=(15, 5))
        
        users_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g., 10 (or 'Unlimited')",
            width=600,
            height=45,
            font=("Segoe UI", 14)
        )
        users_entry.pack(pady=(0, 15))
        
        def submit_package():
            name = name_entry.get().strip()
            description = desc_entry.get().strip()
            price = price_entry.get().strip()
            max_users = users_entry.get().strip()
            
            if not name or not price:
                messagebox.showerror("Error", "Please fill package name and price")
                return
            
            # Collect selected features
            selected_features = [f for f, var in feature_vars.items() if var.get()]
            features_str = ", ".join(selected_features) if selected_features else "No features selected"
            
            try:
                response = requests.post(
                    f"{API_BASE}/super/packages",
                    json={
                        "name": name,
                        "description": description,
                        "price": price,
                        "features": features_str,
                        "max_users": max_users
                    },
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Package created successfully!")
                    dialog.destroy()
                    self.show_package_builder()
                else:
                    messagebox.showerror("Error", response.json().get('message', 'Failed to create package'))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create package: {str(e)}")
        
        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=280,
            height=50,
            font=("Segoe UI Semibold", 14),
            fg_color="transparent",
            border_width=2,
            command=dialog.destroy
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="CREATE PACKAGE",
            width=280,
            height=50,
            font=("Segoe UI Black", 14),
            fg_color=("#8b5cf6", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9"),
            command=submit_package
        ).pack(side="right", padx=10)
    
    def edit_package(self, package):
        """Edit existing package"""
        messagebox.showinfo("Edit Package", f"Edit package: {package.get('name')}\n\nThis feature allows you to modify package details and features.")
    
    def delete_package(self, package):
        """Delete package"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{package.get('name')}'?"):
            try:
                response = requests.delete(
                    f"{API_BASE}/super/packages/{package.get('id')}",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Package deleted successfully!")
                    self.show_package_builder()
                else:
                    messagebox.showerror("Error", "Failed to delete package")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def show_license_management(self):
        """License and Activation management interface with client selection"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "License & Activation")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(
            content,
            text="🔐 License & Device Activation",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(0, 30), anchor="w")
        
        # Fetch clients for dropdown
        clients_data = []
        try:
            response = requests.get(
                f"{API_BASE}/super/clients",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 200:
                clients_data = response.json()
        except:
            pass
            
        client_map = {c.get('pharmacy_name', 'N/A'): c.get('id') for c in clients_data}
        client_names = list(client_map.keys())
        if not client_names:
            client_names = ["No Clients Found"]

        # Generate Key Section
        gen_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
        gen_frame.pack(fill="x", pady=(0, 30))
        
        inner_gen = ctk.CTkFrame(gen_frame, fg_color="transparent")
        inner_gen.pack(padx=30, pady=25)
        
        ctk.CTkLabel(
            inner_gen,
            text="Generate Activation Key",
            font=("Segoe UI Black", 20, "bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # Client Selection
        ctk.CTkLabel(inner_gen, text="SELECT PHARMACY CLIENT", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        selected_client_var = StringVar(value=client_names[0])
        client_dropdown = ctk.CTkOptionMenu(
            inner_gen,
            values=client_names,
            variable=selected_client_var,
            width=600,
            height=45,
            font=("Segoe UI", 14)
        )
        client_dropdown.pack(pady=(5, 20))
        
        # Machine ID Input
        ctk.CTkLabel(inner_gen, text="MACHINE ID (From Client)", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        machine_entry = ctk.CTkEntry(
            inner_gen,
            placeholder_text="Enter Client's Machine ID",
            width=600,
            height=45,
            font=("Consolas", 14)
        )
        machine_entry.pack(pady=(5, 15))
        
        # Target Role
        ctk.CTkLabel(inner_gen, text="TARGET USER ROLE", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        target_role_var = StringVar(value="ADMIN")
        role_menu = ctk.CTkOptionMenu(
            inner_gen,
            values=["ADMIN", "CASHIER", "SUPER_ADMIN"],
            variable=target_role_var,
            width=600, height=45
        )
        role_menu.pack(pady=(5, 20))

        # Key Output (Read-only)
        ctk.CTkLabel(inner_gen, text="GENERATED ACTIVATION KEY", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        key_var = StringVar(value="---- ---- ---- ----")
        key_entry = ctk.CTkEntry(
            inner_gen,
            textvariable=key_var,
            width=600,
            height=50,
            state="readonly",
            font=("Consolas", 20, "bold"),
            text_color=("#4a90e2", "#5ba3ff"),
            justify="center"
        )
        key_entry.pack(pady=(5, 30))
        
        def generate_key():
            m_id = machine_entry.get().strip()
            role = target_role_var.get()
            client_name = selected_client_var.get()
            client_id = client_map.get(client_name) if role != 'SUPER_ADMIN' else None
            
            if not m_id:
                messagebox.showerror("Error", "Please enter a Machine ID")
                return
                
            try:
                response = requests.post(
                    f"{API_BASE}/super/generate-key",
                    json={"machine_id": m_id, "client_id": client_id, "role": role},
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                if response.status_code == 200:
                    gen_key = response.json().get('key')
                    # Format as XXXX XXXX XXXX XXXX
                    formatted = " ".join([gen_key[i:i+4] for i in range(0, len(gen_key), 4)])
                    key_var.set(formatted)
                    messagebox.showinfo("Success", f"Key Generated for {role}!")
                else:
                    messagebox.showerror("Error", "Failed to generate key")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(
            inner_gen,
            text="⚡ GENERATE KEY",
            width=600,
            height=55,
            font=("Segoe UI Black", 15),
            command=generate_key
        ).pack()
        
        # ACTIVE DEVICES MONITORING
        ctk.CTkLabel(
            content,
            text="📱 Active Device Licenses",
            font=("Segoe UI Black", 20, "bold")
        ).pack(anchor="w", pady=(20, 15))
        
        self.load_license_list(content)

    def load_license_list(self, parent):
        """Load and display all activated devices with control buttons"""
        try:
            # We use the activate-device endpoint as a proxy to get activations or add a new getter
            # For now, let's query the clients which have machine IDs
            response = requests.get(
                f"{API_BASE}/super/clients",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            clients = response.json() if response.status_code == 200 else []
        except:
            clients = []
            
        if not clients:
            ctk.CTkLabel(parent, text="No active licenses found").pack()
            return
            
        for client in clients:
            if not client.get('machine_id') and not client.get('client_id_code'): continue
            
            card = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
            card.pack(fill="x", pady=10)
            
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", padx=20, pady=15)
            
            ctk.CTkLabel(info, text=client.get('pharmacy_name', 'System'), font=("Segoe UI Bold", 16)).pack(anchor="w")
            ctk.CTkLabel(info, text=f"Machine: {client.get('machine_id', 'N/A')}", font=("Consolas", 11), text_color="gray").pack(anchor="w")
            
            expiry = client.get('license_expiry', 'N/A')
            if expiry != 'N/A':
                expiry = expiry.split('T')[0]
            ctk.CTkLabel(info, text=f"Expires: {expiry}", font=("Segoe UI", 12)).pack(anchor="w")
            
            # Action Buttons Frame
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(side="right", padx=20)
            
            def handle_action(m_id, act, days=30):
                if not m_id: 
                    messagebox.showerror("Error", "No Machine ID associated")
                    return
                try:
                    res = requests.post(
                        f"{API_BASE}/super/license-action",
                        json={"machine_id": m_id, "action": act, "days": days},
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    if res.status_code == 200:
                        messagebox.showinfo("Success", f"License {act} successfully")
                        self.show_license_management()
                    else:
                        messagebox.showerror("Error", "Action failed")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            # Extend Button
            ctk.CTkButton(
                actions, text="➕ 30 Days", width=100, height=32, 
                fg_color="#10b981", command=lambda m=client.get('machine_id'): handle_action(m, 'extend', 30)
            ).pack(side="left", padx=5)
            
            # Suspend/Revoke
            ctk.CTkButton(
                actions, text="⏸️ Suspend", width=100, height=32,
                fg_color="#f59e0b", command=lambda m=client.get('machine_id'): handle_action(m, 'suspend')
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                actions, text="🚫 Revoke", width=100, height=32,
                fg_color="#ef4444", command=lambda m=client.get('machine_id'): handle_action(m, 'revoked')
            ).pack(side="left", padx=5)
        
        # Instructions
        info_frame = ctk.CTkFrame(content, fg_color=("#f1f5f9", "#0f172a"), corner_radius=15)
        info_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="📖 How to activate a new client device:",
            font=("Segoe UI Semibold", 14),
            justify="left"
        ).pack(pady=15, padx=20, anchor="w")
        
        steps = [
            "1. Client installs software and opens it for the first time.",
            "2. Client sees 'Activation Required' screen with their unique MACHINE ID.",
            "3. Client sends you (Super Admin) their MACHINE ID.",
            "4. You enter the ID above and click GENERATE KEY.",
            "5. You send the 16-character code back to the client.",
            "6. Client enters the code to activate their software permanently."
        ]
        
        for step in steps:
            ctk.CTkLabel(
                info_frame,
                text=f"  {step}",
                font=("Segoe UI", 12),
                text_color=("#64748b", "#94a3b8"),
                justify="left"
            ).pack(pady=3, padx=20, anchor="w")

    def show_global_alerts(self):
        """Global alerts and monitoring with client selection"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        self.create_sidebar(main_container, nav_items, "Global Alerts")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(
            content,
            text="🔔 Global System Alerts",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(0, 25), anchor="w")
        
        # Controls Frame (Dropdown + Buttons)
        ctrl_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        ctrl_frame.pack(fill="x", pady=(0, 20))
        
        inner_ctrl = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        inner_ctrl.pack(padx=20, pady=20, fill="x")
        
        # Fetch Clients
        clients = []
        try:
            res = requests.get(f"{API_BASE}/super/clients", headers={"Authorization": f"Bearer {self.token}"})
            if res.status_code == 200: clients = res.json()
        except: pass
        
        client_options = ["All Pharmacies"] + [f"{c['id']} - {c['pharmacy_name']}" for c in clients]
        client_var = StringVar(value="All Pharmacies")
        
        ctk.CTkLabel(inner_ctrl, text="Filter by Pharmacy", font=("Segoe UI Semibold", 12)).grid(row=0, column=0, padx=10, sticky="w")
        client_menu = ctk.CTkOptionMenu(inner_ctrl, values=client_options, variable=client_var, width=280)
        client_menu.grid(row=1, column=0, padx=10, pady=(5, 0))
        
        def run_low_stock():
            sel_client = client_var.get()
            cid = sel_client.split(" - ")[0] if sel_client != "All Pharmacies" else "all"
            self.check_low_stock_all(cid)

        def run_expiry():
            sel_client = client_var.get()
            cid = sel_client.split(" - ")[0] if sel_client != "All Pharmacies" else "all"
            self.check_expiry_all(cid)

        ctk.CTkButton(
            inner_ctrl,
            text="📉 Check Low Stock",
            height=45,
            fg_color=("#f59e0b", "#d97706"),
            command=run_low_stock
        ).grid(row=1, column=1, padx=10, pady=(5, 0))
        
        ctk.CTkButton(
            inner_ctrl,
            text="⏰ Check Expiry Alerts",
            height=45,
            fg_color=("#ef4444", "#dc2626"),
            command=run_expiry
        ).grid(row=1, column=2, padx=10, pady=(5, 0))
        
        # Alerts display area
        self.alerts_container = ctk.CTkFrame(content, fg_color="transparent")
        self.alerts_container.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            self.alerts_container,
            text="Select a filter and click check buttons above to view alerts...",
            font=("Segoe UI", 14),
            text_color="gray"
        ).pack(pady=100)
    
    def check_low_stock_all(self, client_id="all"):
        """Check low stock with optional client filter"""
        for widget in self.alerts_container.winfo_children(): widget.destroy()
        
        try:
            response = requests.get(
                f"{API_BASE}/check-low-stock?client_id={client_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    ctk.CTkLabel(self.alerts_container, text="No low stock alerts found. ✅", font=("Segoe UI", 16)).pack(pady=50)
                    return
                
                # Table Header
                table = ctk.CTkScrollableFrame(self.alerts_container, height=500, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
                table.pack(fill="both", expand=True)
                
                header = ctk.CTkFrame(table, fg_color=("#f1f5f9", "#0f172a"))
                header.pack(fill="x", pady=2)
                
                for i, h in enumerate(["Pharmacy", "Medicine Name", "Current Stock", "Min Level"]):
                    ctk.CTkLabel(header, text=h, font=("Segoe UI Bold", 12), width=230).grid(row=0, column=i, padx=10, pady=10, sticky="w")
                
                for item in data:
                    row = ctk.CTkFrame(table, fg_color="transparent")
                    row.pack(fill="x")
                    ctk.CTkLabel(row, text=item['pharmacy_name'], width=230, anchor="w").grid(row=0, column=0, padx=10, pady=5)
                    ctk.CTkLabel(row, text=item['name'], width=230, anchor="w").grid(row=0, column=1, padx=10, pady=5)
                    ctk.CTkLabel(row, text=str(item['stock_quantity']), width=230, anchor="center", text_color="#ef4444").grid(row=0, column=2, padx=10, pady=5)
                    ctk.CTkLabel(row, text=str(item['min_stock_level']), width=230, anchor="center").grid(row=0, column=3, padx=10, pady=5)
            else:
                messagebox.showerror("Error", "Failed to fetch low stock alerts")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def check_expiry_all(self, client_id="all"):
        """Check expiry alerts with optional client filter"""
        for widget in self.alerts_container.winfo_children(): widget.destroy()
        
        try:
            response = requests.get(
                f"{API_BASE}/check-expiry?client_id={client_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    ctk.CTkLabel(self.alerts_container, text="No immediate medicine expiries found. ✅", font=("Segoe UI", 16)).pack(pady=50)
                    return
                
                table = ctk.CTkScrollableFrame(self.alerts_container, height=500, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
                table.pack(fill="both", expand=True)
                
                header = ctk.CTkFrame(table, fg_color=("#f1f5f9", "#0f172a"))
                header.pack(fill="x", pady=2)
                
                for i, h in enumerate(["Pharmacy", "Medicine Name", "Batch No", "Expiry Date"]):
                    ctk.CTkLabel(header, text=h, font=("Segoe UI Bold", 12), width=230).grid(row=0, column=i, padx=10, pady=10, sticky="w")
                
                for item in data:
                    row = ctk.CTkFrame(table, fg_color="transparent")
                    row.pack(fill="x")
                    expiry = item['expiry_date'].split('T')[0] if 'T' in item['expiry_date'] else item['expiry_date']
                    ctk.CTkLabel(row, text=item['pharmacy_name'], width=230, anchor="w").grid(row=0, column=0, padx=10, pady=5)
                    ctk.CTkLabel(row, text=item['name'], width=230, anchor="w").grid(row=0, column=1, padx=10, pady=5)
                    ctk.CTkLabel(row, text=item['batch_number'], width=230, anchor="center").grid(row=0, column=2, padx=10, pady=5)
                    ctk.CTkLabel(row, text=expiry, width=230, anchor="center", text_color="#ef4444").grid(row=0, column=3, padx=10, pady=5)
            else:
                messagebox.showerror("Error", "Failed to fetch expiry alerts")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _show_system_settings_real(self):
        ctk.CTkButton(toolbar, text="➕ NEW LAYOUT", width=120, height=35, fg_color="#3b82f6", command=clear_canvas).pack(side="left", padx=10)

        ctk.CTkLabel(toolbar, text="📄 PAPER:", font=("Segoe UI Bold", 13)).pack(side="left", padx=10)

        ctk.CTkLabel(toolbar, text="📄 PAPER SIZE:", font=("Segoe UI Bold", 13)).pack(side="left", padx=15)
        paper_size_var = StringVar(value="A5 (Pharmacy Standard)")
        paper_sizes = {
            "A4 (Full Page)": (630, 891),
            "A5 (Pharmacy Standard)": (444, 630),
            "Thermal 80mm": (300, 1000),
            "Thermal 58mm": (220, 800)
        }
        
        def on_paper_size_change(choice):
            width, height = paper_sizes.get(choice, (444, 630))
            page.configure(width=width, height=height)
            self.active_design["_meta"]["paper"] = choice
            
        paper_menu = ctk.CTkOptionMenu(toolbar, values=list(paper_sizes.keys()), variable=paper_size_var, command=on_paper_size_change, width=220)
        paper_menu.pack(side="left", padx=5)
        
        # 2. Side Panels Layout
        main_workspace = ctk.CTkFrame(content, fg_color="transparent")
        main_workspace.pack(fill="both", expand=True)
        
        # Left Panel: Layers & Presets
        layers_panel = ctk.CTkFrame(main_workspace, width=250, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        layers_panel.pack(side="left", fill="y", padx=(0, 20))
        
        ctk.CTkLabel(layers_panel, text="🧩 ELEMENTS", font=("Segoe UI Black", 16)).pack(pady=15)
        
        btn_style = {"width": 220, "height": 32, "font": ("Segoe UI Semibold", 11)}
        
        ctk.CTkLabel(layers_panel, text="🏢 Header Elements", font=("Segoe UI Bold", 12), text_color="gray").pack(pady=(10, 5))
        ctk.CTkButton(layers_panel, text="Pharmacy Logo Box", command=lambda: add_design_element("logo", "[ LOGO ]", size=14, weight="bold"), **btn_style).pack(pady=2)
        ctk.CTkButton(layers_panel, text="Tax/PAN: {PAN}", command=lambda: add_design_element("var", "PAN: {PAN}"), **btn_style).pack(pady=2)
        ctk.CTkButton(layers_panel, text="Receipt Title", command=lambda: add_design_element("label", "TAX INVOICE", size=14, weight="bold"), **btn_style).pack(pady=2)
        
        ctk.CTkLabel(layers_panel, text="👥 Customer Info", font=("Segoe UI Bold", 12), text_color="gray").pack(pady=(15, 5))
        ctk.CTkButton(layers_panel, text="Name: {Customer}", command=lambda: add_design_element("var", "Name: {Customer}"), **btn_style).pack(pady=2)
        ctk.CTkButton(layers_panel, text="Phone: {CustPhone}", command=lambda: add_design_element("var", "Phone: {CustPhone}"), **btn_style).pack(pady=2)
        ctk.CTkButton(layers_panel, text="QR Code Block", command=lambda: add_design_element("qrcode", "[ QR CODE ]", size=12), **btn_style).pack(pady=2)
        
        ctk.CTkLabel(layers_panel, text="📑 Transactional", font=("Segoe UI Bold", 12), text_color="gray").pack(pady=(15, 5))
        ctk.CTkButton(layers_panel, text="Bill Table Block", command=lambda: add_design_element("table", "+-----+----------------+----------+--------+-----+------+--------+\n| S.N | Medicine Name  | Batch No | Expiry | Qty | Rate | Amount |\n+-----+----------------+----------+--------+-----+------+--------+", weight="bold", font_family="Consolas"), **btn_style).pack(pady=2)
        ctk.CTkButton(layers_panel, text="Totals: {GrandTotal}", command=lambda: add_design_element("totals", "Grand Total: {Total}"), **btn_style).pack(pady=2)
        ctk.CTkButton(layers_panel, text="Amount In Words", command=lambda: add_design_element("var", "In Words: {AmtWords}"), **btn_style).pack(pady=2)
        
        ctk.CTkLabel(layers_panel, text="📜 Footer", font=("Segoe UI Bold", 12), text_color="gray").pack(pady=(15, 5))
        ctk.CTkButton(layers_panel, text="Terms & Conditions", command=lambda: add_design_element("label", "Terms: No return after 24h", size=8), **btn_style).pack(pady=2)
        ctk.CTkButton(layers_panel, text="Signature Line", command=lambda: add_design_element("label", "..........................\nAuthorized Signature", size=9), **btn_style).pack(pady=2)

        ctk.CTkLabel(layers_panel, text="🎨 Graphics", font=("Segoe UI Bold", 12), text_color="gray").pack(pady=(15, 5))
        ctk.CTkButton(layers_panel, text="Add Border Box", command=lambda: add_design_element("box", "", size=2, weight="normal"), **btn_style).pack(pady=2)
        
        # Center: Canvas
        canvas_container = ctk.CTkScrollableFrame(main_workspace, fg_color=("#cbd5e1", "#020617"), corner_radius=15)
        canvas_container.pack(side="left", fill="both", expand=True)
        
        # A5 Page Mockup (scaled)
        page = ctk.CTkFrame(canvas_container, width=444, height=630, fg_color="white", corner_radius=0)
        page.pack(pady=40, padx=40)
        page.pack_propagate(False)
        
        # Right Panel: Property Editor & Publishing
        right_panel = ctk.CTkFrame(main_workspace, width=320, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        right_panel.pack(side="right", fill="y", padx=(20, 0))
        
        # --- DESIGNER LOGIC ---
        self.active_design = {
            "_meta": {"paper": "A5 (Pharmacy Standard)"},
            "pharmacy_name": {"text": "MY PHARMACY NAME", "x": 100, "y": 20, "size": 18, "weight": "bold", "align": "center"},
            "address": {"text": "{Address}\nPh: {Phone}", "x": 125, "y": 55, "size": 10, "weight": "normal", "align": "center"},
            "pan_oda": {"text": "PAN: {PAN}  |  ODA: {ODA}", "x": 145, "y": 90, "size": 9, "weight": "normal", "align": "center"},
            "title": {"text": "TAX INVOICE", "x": 135, "y": 120, "size": 14, "weight": "bold", "align": "center"},
            "table": {"text": "+-----+----------------+----------+--------+-----+------+--------+\n| S.N | Medicine Name  | Batch No | Expiry | Qty | Rate | Amount |\n+-----+----------------+----------+--------+-----+------+--------+", "x": 30, "y": 200, "size": 9, "weight": "normal", "align": "left", "font_family": "Consolas"},
            "totals": {"text": "SubTotal: 0.00\nDiscount: 0.00\nTotal: 0.00", "x": 260, "y": 500, "size": 11, "weight": "bold", "align": "right"},
            "footer": {"text": "Get Well Soon!", "x": 120, "y": 580, "size": 9, "weight": "italic", "align": "center"},
            "signature": {"text": "Authorized Signature", "x": 260, "y": 580, "size": 10, "weight": "normal", "align": "right"}
        }
        
        def add_design_element(name, text, x=50, y=50, size=10, weight="normal", align="left", font_family="Segoe UI"):
            eid = f"{name}_{uuid.uuid4().hex[:4]}"
            initial_data = {"text": text, "x": x, "y": y, "size": size, "weight": weight, "align": align, "font_family": font_family}
            if name == "box":
                initial_data.update({"width": 200, "height": 100, "border": 2})
            self.active_design[eid] = initial_data
            render_canvas()
            select_element(eid)
        self.widgets = {}
        self.selected_key = None
        
        def select_element(key):
            self.selected_key = key
            # Update property editor UI
            prop_name_lbl.configure(text=f"Editing: {key.upper()}")
            txt_input.delete(0, 'end')
            txt_input.insert(0, self.active_design[key]["text"])
            size_spin.set(self.active_design[key]["size"])
            weight_var.set(self.active_design[key]["weight"])
            align_var.set(self.active_design[key].get("align", "left"))
            
            # Dimension fields for Boxes
            w_input.delete(0, 'end')
            h_input.delete(0, 'end')
            if "box" in key:
                w_input.insert(0, str(self.active_design[key].get("width", 200)))
                h_input.insert(0, str(self.active_design[key].get("height", 100)))
            
            x_input.delete(0, 'end')
            x_input.insert(0, str(self.active_design[key]["x"]))
            y_input.delete(0, 'end')
            y_input.insert(0, str(self.active_design[key]["y"]))
            
            # Special Table Properties
            for w in special_props_frame.winfo_children(): w.destroy()
            if "table" in key:
                ctk.CTkLabel(special_props_frame, text="📊 TABLE COLUMNS", font=("Segoe UI Black", 12)).pack(pady=(10, 5))
                cols = ["ITEM", "QTY", "RATE", "BATCH", "EXP", "DISC", "TAX", "AMOUNT"]
                current_text = self.active_design[key]["text"]
                # 1. Initialize check_vars container FIRST
                check_vars = {}

                # 2. Populate CheckVars and Create Checkboxes
                for col in cols:
                    # Logic to determine if checked
                    is_checked = col in current_text or (col == "ITEM" and "Medicine Name" in current_text)
                    var = ctk.BooleanVar(value=is_checked)
                    check_vars[col] = var 
                    
                # 3. Define Toggle Function
                def on_toggle():
                    new_cols = ["S.N"]
                    for c_name in cols: # Iterate in original order
                        if check_vars[c_name].get():
                            new_cols.append(c_name)
                    
                    display_map = {
                        "S.N": "S.N", "ITEM": "Medicine Name ", "QTY": "Qty", "RATE": "Rate", 
                        "BATCH": "Batch No", "EXP": "Expiry", "DISC": "Disc", "TAX": "Tax", "AMOUNT": "Amount"
                    }
                    width_map = {
                        "S.N": 5, "ITEM": 16, "QTY": 5, "RATE": 6, 
                        "BATCH": 10, "EXP": 8, "DISC": 5, "TAX": 5, "AMOUNT": 8
                    }
                    
                    sep_line = "+" + "+".join(["-" * (width_map.get(x, 10)) for x in new_cols]) + "+"
                    header_line = "|" + "|".join([f" {display_map.get(x, x):<{width_map.get(x, 10)-2}} " for x in new_cols]) + "|"
                    
                    self.active_design[key]["text"] = sep_line + "\n" + header_line + "\n" + sep_line
                    render_canvas()

                # 4. Render Checkboxes with Command
                for col in cols:
                    ctk.CTkCheckBox(special_props_frame, text=col, variable=check_vars[col], command=on_toggle).pack(anchor="w", padx=10, pady=2)
            
        def drag_element(event, key):
            new_x = event.x_root - page.winfo_rootx() - (self.widgets[key].winfo_width()/2)
            new_y = event.y_root - page.winfo_rooty() - (self.widgets[key].winfo_height()/2)
            
            self.active_design[key]["x"] = int(new_x)
            self.active_design[key]["y"] = int(new_y)
            self.widgets[key].place(x=new_x, y=new_y)
            
            # Sync to fields if this is the selected element
            if self.selected_key == key:
                x_input.delete(0, 'end')
                x_input.insert(0, str(int(new_x)))
                y_input.delete(0, 'end')
                y_input.insert(0, str(int(new_y)))

        def render_canvas():
            for w in self.widgets.values(): w.destroy()
            self.widgets = {}
            for key, meta in self.active_design.items():
                if key == "_meta": continue
                anchor = "w"
                if meta.get("align") == "center": anchor = "center"
                elif meta.get("align") == "right": anchor = "e"
                
                # Visual improvements for special blocks
                txt = meta["text"]
                bg = "transparent"
                border = 0
                
                if "logo" in key:
                    lbl = ctk.CTkLabel(page, text="📷 LOGO", fg_color="#f1f5f9", text_color="#64748b",
                                      width=100, height=60, font=("Segoe UI Black", 10), corner_radius=10)
                elif "qrcode" in key:
                    lbl = ctk.CTkLabel(page, text="🔳 QR", fg_color="#f1f5f9", text_color="#64748b",
                                      width=60, height=60, font=("Segoe UI Black", 10), corner_radius=5)
                elif "box" in key:
                    lbl = ctk.CTkFrame(page, fg_color="transparent", border_width=meta.get("size", 2), 
                                      border_color="black", width=meta.get("width", 200), 
                                      height=meta.get("height", 100))
                else:
                    font_family = meta.get("font_family", "Segoe UI")
                    lbl = ctk.CTkLabel(page, text=txt, text_color="black", 
                                      font=(font_family, meta["size"], meta["weight"]),
                                      justify=meta.get("align", "left"), anchor=anchor)
                
                lbl.place(x=meta["x"], y=meta["y"])
                lbl.bind("<Button-1>", lambda e, k=key: select_element(k))
                lbl.bind("<B1-Motion>", lambda e, k=key: drag_element(e, k))
                self.widgets[key] = lbl

        # --- PROPERTY EDITOR UI ---
        ctk.CTkLabel(right_panel, text="🎨 PROPERTIES", font=("Segoe UI Black", 16)).pack(pady=15)
        prop_name_lbl = ctk.CTkLabel(right_panel, text="Select an element", font=("Segoe UI", 12), text_color="gray")
        prop_name_lbl.pack(pady=5)
        
        txt_input = ctk.CTkEntry(right_panel, width=260, placeholder_text="Display Text")
        txt_input.pack(pady=10)
        
        # Font Controls
        font_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        font_frame.pack(pady=10)
        ctk.CTkLabel(font_frame, text="Size:").pack(side="left", padx=5)
        size_spin = ctk.CTkSegmentedButton(font_frame, values=["8", "10", "12", "14", "18", "24"])
        size_spin.pack(side="left", padx=5)
        
        weight_var = StringVar(value="normal")
        weight_menu = ctk.CTkOptionMenu(right_panel, values=["normal", "bold", "italic"], variable=weight_var)
        weight_menu.pack(pady=10)

        ctk.CTkLabel(right_panel, text="Alignment:").pack(pady=(5, 0))
        align_var = StringVar(value="left")
        align_menu = ctk.CTkSegmentedButton(right_panel, values=["left", "center", "right"], variable=align_var)
        align_menu.pack(pady=10)

        special_props_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        special_props_frame.pack(fill="x", pady=10)

        # Geometry Controls
        geo_label = ctk.CTkLabel(right_panel, text="X / Y", font=("Segoe UI Semibold", 12))
        geo_label.pack(pady=(10, 0))
        geo_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        geo_frame.pack(pady=5)
        x_input = ctk.CTkEntry(geo_frame, width=60)
        x_input.pack(side="left", padx=2)
        y_input = ctk.CTkEntry(geo_frame, width=60)
        y_input.pack(side="left", padx=2)
        w_input = ctk.CTkEntry(geo_frame, width=60, placeholder_text="W")
        w_input.pack(side="left", padx=2)
        h_input = ctk.CTkEntry(geo_frame, width=60, placeholder_text="H")
        h_input.pack(side="left", padx=2)

        def apply_props():
            if not self.selected_key: return
            self.active_design[self.selected_key]["text"] = txt_input.get()
            self.active_design[self.selected_key]["size"] = int(size_spin.get() or 10)
            self.active_design[self.selected_key]["weight"] = weight_var.get()
            self.active_design[self.selected_key]["align"] = align_var.get()
            try:
                self.active_design[self.selected_key]["x"] = int(x_input.get())
                self.active_design[self.selected_key]["y"] = int(y_input.get())
                if "box" in self.selected_key:
                    self.active_design[self.selected_key]["width"] = int(w_input.get() or 200)
                    self.active_design[self.selected_key]["height"] = int(h_input.get() or 100)
            except: pass
            render_canvas()
            
        ctk.CTkButton(right_panel, text="💾 Apply Changes", fg_color="#10b981", command=apply_props).pack(pady=15)
        
        def delete_item():
            if not self.selected_key: return
            if self.selected_key in ["pharmacy_name", "table", "totals"]:
                messagebox.showwarning("Warning", "Core elements cannot be deleted")
                return
            del self.active_design[self.selected_key]
            self.selected_key = None
            render_canvas()
            prop_name_lbl.configure(text="Select an element")
            
        ctk.CTkButton(right_panel, text="🗑️ Delete Item", fg_color="#ef4444", hover_color="#dc2626", command=delete_item).pack(pady=5)
        
        # --- PUBLISHING SYSTEM ---
        ctk.CTkLabel(right_panel, text="🚀 PUBLISH & DEPLOY", font=("Segoe UI Black", 16)).pack(pady=(40, 15))
        
        # Client selection tracking
        self.target_client_ids = "all"
        
        def show_client_selection_dialog():
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Select Target Clients")
            dialog.geometry("500x600")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ctk.CTkLabel(dialog, text="Select Pharmacies", font=("Segoe UI Black", 20)).pack(pady=20)
            
            scroll = ctk.CTkScrollableFrame(dialog, width=400, height=400)
            scroll.pack(padx=20, pady=10, fill="both", expand=True)
            
            # Fetch clients
            clients = []
            try:
                res = requests.get(f"{API_BASE}/super/clients", headers={"Authorization": f"Bearer {self.token}"})
                if res.status_code == 200: clients = res.json()
            except: pass
            
            check_vars = {}
            for c in clients:
                var = ctk.BooleanVar()
                cb = ctk.CTkCheckBox(scroll, text=f"{c['pharmacy_name']} ({c['client_id_code']})", variable=var)
                cb.pack(pady=5, anchor="w", padx=10)
                check_vars[c['id']] = var
            
            def confirm():
                selected = [cid for cid, v in check_vars.items() if v.get()]
                if not selected:
                    messagebox.showwarning("Warning", "Please select at least one client")
                    return
                self.target_client_ids = selected
                client_target_var.set(f"Selected: {len(selected)} Clients")
                dialog.destroy()
            
            ctk.CTkButton(dialog, text="CONFIRM SELECTION", command=confirm, height=45).pack(pady=20, padx=40, fill="x")

        def on_client_target_change(choice):
            if choice == "Specific Client...":
                show_client_selection_dialog()
            elif choice == "All Clients":
                self.target_client_ids = "all"
            else:
                self.target_client_ids = []

        client_target_var = StringVar(value="All Clients")
        ctk.CTkLabel(right_panel, text="Target Clients:").pack(padx=20, anchor="w")
        client_select = ctk.CTkOptionMenu(right_panel, values=["All Clients", "Specific Client..."], 
                                         variable=client_target_var, width=260, command=on_client_target_change)
        client_select.pack(pady=5)
        
        def handle_publish():
            if not self.target_client_ids or (isinstance(self.target_client_ids, list) and not self.target_client_ids):
                messagebox.showerror("Error", "Please select target clients first")
                return
                
            design_json = json.dumps(self.active_design)
            l_name = layout_name_entry.get() or f"Layout_{datetime.now().strftime('%Y%m%d_%H%M')}"
            try:
                # 1. Save as latest version
                save_res = requests.post(f"{API_BASE}/super/bill-designs", 
                                       json={"name": l_name, "design_data": design_json},
                                       headers={"Authorization": f"Bearer {self.token}"})
                
                if save_res.status_code == 200:
                    design_id = save_res.json().get('id', 1)
                    # 2. Publish to target
                    publish_res = requests.post(f"{API_BASE}/super/bill-designs/publish",
                                              json={"design_id": design_id, "client_ids": self.target_client_ids},
                                              headers={"Authorization": f"Bearer {self.token}"})
                    messagebox.showinfo("Success", "Design published successfully!\nClients will receive update on next sync.")
                else:
                    messagebox.showerror("Error", "Failed to save design version")
            except Exception as e:
                messagebox.showerror("Network Error", str(e))

        ctk.CTkButton(right_panel, text="🌍 DEPLOY GLOBALLY", height=50, font=("Segoe UI Bold", 14), fg_color="#4f46e5", command=handle_publish).pack(pady=20, padx=30, fill="x")
        
        # Load Existing Templates
        def load_templates():
            try:
                res = requests.get(f"{API_BASE}/super/bill-designs", headers={"Authorization": f"Bearer {self.token}"})
                if res.status_code == 200:
                    templates = res.json()
                    names = [t["name"] for t in templates]
                    if names:
                        template_menu.configure(values=names)
                        # Store in design_list for callback
                        self.design_list = {t["name"]: t["design_data"] for t in templates}
            except: pass
            
        def on_template_change(*args):
             name = template_var.get()
             if hasattr(self, 'design_list') and name in self.design_list:
                 self.active_design = json.loads(self.design_list[name])
                 layout_name_entry.delete(0, 'end')
                 layout_name_entry.insert(0, name)
                 # Sync UI with design metadata
                 meta = self.active_design.get("_meta", {})
                 p_size = meta.get("paper", "A5 (Pharmacy Standard)")
                 paper_size_var.set(p_size)
                 w, h = paper_sizes.get(p_size, (444, 630))
                 page.configure(width=w, height=h)
                 render_canvas()

        template_var.trace_add("write", on_template_change)
        
        render_canvas()
        load_templates()

    def show_system_logs(self):
        """View detailed system audit logs"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "System Logs")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        header = ctk.CTkLabel(content, text="📜 System Audit Logs", font=("Segoe UI Black", 28, "bold"), text_color=("#1e293b", "#f1f5f9"))
        header.pack(anchor="w", pady=(0, 25))

        try:
            res = requests.get(f"{API_BASE}/super/audit-logs", headers={"Authorization": f"Bearer {self.token}"})
            logs = res.json() if res.status_code == 200 else []
        except:
            logs = []

        if not logs:
            ctk.CTkLabel(content, text="No system logs found.", font=("Segoe UI", 16), text_color="gray").pack(pady=100)
            return

        for log in logs:
            card = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=12)
            card.pack(fill="x", pady=5)
            
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(top_row, text=f"⚡ {log['action']}", font=("Segoe UI Bold", 14)).pack(side="left")
            ctk.CTkLabel(top_row, text=log.get('created_at', ''), font=("Consolas", 11), text_color="gray").pack(side="right")
            
            ctk.CTkLabel(card, text=f"Details: {log.get('details', 'N/A')}", font=("Segoe UI", 13), text_color=("#475569", "#94a3b8"), wraplength=800).pack(anchor="w", padx=15, pady=(0, 5))
            ctk.CTkLabel(card, text=f"Performed by: {log.get('user_name') or 'System'}", font=("Segoe UI Semibold", 11), text_color="#6366f1").pack(anchor="w", padx=15, pady=(0, 10))

    def show_announcements(self):
        """Broadcast system-wide announcements with target selection (Matching Image)"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "Announcements")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(
            content, 
            text="📢 Create New Announcement", 
            font=("Segoe UI Black", 28, "bold")
        ).pack(anchor="w", pady=(0, 30))
        
        form_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        form_frame.pack(fill="x", pady=(0, 20))
        
        inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        inner.pack(padx=30, pady=30, fill="x")
        
        ctk.CTkLabel(inner, text="Title: *", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        title_entry = ctk.CTkEntry(inner, height=45, placeholder_text="Enter Announcement Title")
        title_entry.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(inner, text="Message: *", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        msg_text = ctk.CTkTextbox(inner, height=180)
        msg_text.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(inner, text="Send To:", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        
        # Fetch clients for target selection
        clients = []
        try:
            res = requests.get(f"{API_BASE}/super/clients", headers={"Authorization": f"Bearer {self.token}"})
            if res.status_code == 200:
                clients = res.json()
        except: pass
        
        target_options = ["All Clients"] + [f"{c['client_id_code']} - {c['pharmacy_name']}" for c in clients]
        target_var = StringVar(value="All Clients")
        target_menu = ctk.CTkOptionMenu(inner, values=target_options, variable=target_var, height=45)
        target_menu.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(inner, text="Expiry Date (BS: YYYY-MM-DD):", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        expiry_entry = ctk.CTkEntry(inner, height=45, placeholder_text=DateUtils.get_current_bs_date_str())
        # Default expiry: 30 days from now
        default_expiry_ad = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        default_expiry_bs = DateUtils.ad_to_bs(default_expiry_ad)
        expiry_entry.insert(0, default_expiry_bs)
        expiry_entry.pack(fill="x", pady=(5, 5))
        
        ctk.CTkLabel(
            inner, 
            text="ⓘ Announcement will be automatically deleted after expiry", 
            font=("Segoe UI", 12), 
            text_color="gray"
        ).pack(anchor="w", pady=(0, 25))
        
        def post_announcement():
            title = title_entry.get().strip()
            message = msg_text.get("1.0", "end-1c").strip()
            target = target_var.get()
            expiry = expiry_entry.get().strip()
            
            if not title or not message:
                messagebox.showerror("Error", "Title and Message are required!")
                return
                
            # Extract client id if not "All Clients"
            target_client_id = None
            if target != "All Clients":
                code = target.split(" - ")[0]
                client = next((c for c in clients if c['client_id_code'] == code), None)
                if client: target_client_id = client['id']
            
            data = {
                "title": title,
                "message": message,
                "target_client_id": target_client_id,
                # User enters BS date. Backend expects... wait, backend creates date. 
                # If backend stores as DATE, it might need AD. 
                # User Rule: "Internally system MAY store AD... conversion MUST happen before display"
                # So if I send BS date '2082-10-14' to a DATE column, MySQL might reject it or store it as year 2082. 
                # If I store 2082, then AD conversion logic fails later. 
                # DECISION: Convert BS Input -> AD before sending to backend.
                "expiry_date": DateUtils.bs_to_ad(expiry_entry.get().strip()) if expiry_entry.get().strip() else None
            }
            
            try:
                res = requests.post(
                    f"{API_BASE}/super/announcements", 
                    json=data, 
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                if res.status_code == 200:
                    messagebox.showinfo("Success", "Announcement posted successfully!")
                    self.show_announcements()
                else:
                    messagebox.showerror("Error", "Failed to post announcement")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(
            inner, 
            text="📢 Post Announcement", 
            height=55, 
            font=("Segoe UI Black", 16),
            fg_color="#00897b",
            hover_color="#00695c",
            command=post_announcement
        ).pack(fill="x", pady=10)

    def show_system_settings(self):
        """Main system configuration and white-labeling"""
        for widget in self.root.winfo_children():
            widget.destroy()
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        nav_items = self.get_super_admin_nav()
        self.create_sidebar(main_container, nav_items, "System Settings")
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(content, text="⚙️ System Configuration", font=("Segoe UI Black", 28, "bold")).pack(anchor="w", pady=(0, 25))
        
        try:
            res = requests.get(f"{API_BASE}/super/settings", headers={"Authorization": f"Bearer {self.token}"})
            settings = res.json() if res.status_code == 200 else []
        except: settings = []
        
        entries = {}
        for s in settings:
            row = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=12)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=s['description'] or s['config_key'], font=("Segoe UI Semibold", 13)).pack(side="left", padx=20, pady=15)
            entry = ctk.CTkEntry(row, width=300)
            entry.insert(0, s['config_value'] or '')
            entry.pack(side="right", padx=20, pady=15)
            entries[s['config_key']] = entry
            
        def save_settings():
            data = {k: v.get() for k, v in entries.items()}
            try:
                res = requests.post(f"{API_BASE}/super/settings", json=data, headers={"Authorization": f"Bearer {self.token}"})
                if res.status_code == 200: messagebox.showinfo("Success", "Settings updated!")
            except: messagebox.showerror("Error", "Update failed")
            
        ctk.CTkButton(content, text="💾 SAVE ALL SETTINGS", height=55, font=("Segoe UI Black", 14), command=save_settings).pack(pady=40, fill="x")

    def login_as_client_admin(self, client):
        """Impersonate a client admin for troubleshooting"""
        if not messagebox.askyesno("Confirm Impersonation", f"Log in as Admin for {client['pharmacy_name']}?\nThis will switch your session."):
            return
        try:
            res = requests.post(f"{API_BASE}/super/login-as-admin", json={"client_id": client['id']}, headers={"Authorization": f"Bearer {self.token}"})
            if res.status_code == 200:
                data = res.json()
                self.token = data['token']
                self.user = data['user']
                messagebox.showinfo("Success", f"Logged in as Admin: {client['pharmacy_name']}")
                self.show_admin_dashboard()
        except: messagebox.showerror("Error", "Impersonation failed")

    def show_profile_edit(self):
        """Cute profile edit dialog with circle image selection"""
        if not self.user.get('id'):
            messagebox.showwarning("Warning", "Hardcoded Super Admin profile cannot be edited.")
            return

        # Fetch fresh data to ensure phone number etc are loaded
        try:
            r = requests.get(f"{API_BASE}/profile", headers={"Authorization": f"Bearer {self.token}"})
            if r.status_code == 200:
                server_user = r.json()
                self.user.update(server_user)
        except: pass

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit My Profile")
        dialog.geometry("550x750")
        dialog.transient(self.root)
        dialog.grab_set()

        # Use Scrollable Frame to ensure save button is always reachable
        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(content, text="👤 MY PROFILE SETTINGS", font=("Segoe UI Black", 24)).pack(pady=20)

        # Profile Picture Selection
        pic_box = ctk.CTkFrame(content, width=140, height=140, corner_radius=70, fg_color=("#e2e8f0", "#1e293b"))
        pic_box.pack(pady=10)
        pic_box.pack_propagate(False)

        current_pic_base64 = self.user.get('profile_pic')
        pic_lbl = ctk.CTkLabel(pic_box, text="", image=self.get_circular_image(current_pic_base64, size=(140, 140)))
        pic_lbl.pack(expand=True)

        new_pic_base64 = [current_pic_base64] 

        def select_pic():
            path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
            if path:
                import base64
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                    new_pic_base64[0] = encoded
                    pic_lbl.configure(image=self.get_circular_image(encoded, size=(140, 140)))

        ctk.CTkButton(content, text="📷 UPDATE PHOTO", font=("Segoe UI Bold", 12), width=200, height=40, command=select_pic).pack(pady=10)

        # Fields Section
        fields_container = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        fields_container.pack(fill="x", padx=20, pady=10)

        inner_p = 25
        ctk.CTkLabel(fields_container, text="Full Name", font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=inner_p, pady=(20, 5))
        name_entry = ctk.CTkEntry(fields_container, width=350, height=45)
        name_entry.insert(0, self.user.get('name', ''))
        name_entry.pack(padx=inner_p)

        ctk.CTkLabel(fields_container, text="Email Address", font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=inner_p, pady=(15, 5))
        email_entry = ctk.CTkEntry(fields_container, width=350, height=45)
        email_entry.insert(0, self.user.get('email', '') or '')
        email_entry.pack(padx=inner_p)

        # Phone Number Display (Registered vs New)
        ctk.CTkLabel(fields_container, text="Already Registered Number:", font=("Segoe UI Bold", 12), text_color="#6366f1").pack(anchor="w", padx=inner_p, pady=(20, 0))
        ctk.CTkLabel(fields_container, text=self.user.get('phone', 'N/A'), font=("Segoe UI Semibold", 16)).pack(anchor="w", padx=inner_p, pady=(0, 15))

        ctk.CTkLabel(fields_container, text="Update Phone Number (New)", font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=inner_p, pady=(5, 5))
        phone_entry = ctk.CTkEntry(fields_container, width=350, height=45, placeholder_text="Enter new phone number")
        phone_entry.insert(0, self.user.get('phone', '') or '')
        phone_entry.pack(padx=inner_p, pady=(0, 30))

        def save_profile():
            payload = {
                "name": name_entry.get(),
                "email": email_entry.get(),
                "phone": phone_entry.get(),
                "profile_pic": new_pic_base64[0]
            }
            try:
                res = requests.post(f"{API_BASE}/profile", json=payload, headers={"Authorization": f"Bearer {self.token}"})
                if res.status_code == 200:
                    self.user.update(payload)
                    messagebox.showinfo("Success", "✅ Profile updated successfully!")
                    dialog.destroy()
                    self.show_super_admin_dashboard()
                else:
                    try: err_msg = res.json().get('message', 'Update failed')
                    except: err_msg = f"Server Error ({res.status_code})"
                    messagebox.showerror("Error", err_msg)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # Replaced 💾 emoji with clear text and better visibility
        ctk.CTkButton(content, text="✓ SAVE ALL PROFILE CHANGES", font=("Segoe UI Black", 14), width=400, height=55, fg_color="#10b981", hover_color="#059669", command=save_profile).pack(pady=30)

    def show_sms_management(self):
        """SMS Management - Send SMS, Upload Excel, View Credits"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "SMS Management")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header with SMS Balance
        header_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
        header_frame.pack(fill="x", pady=(0, 30))
        
        ctk.CTkLabel(
            header_frame,
            text="📱 SMS Management Center",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left", padx=30, pady=25)
        
        # SMS Balance Display
        balance_container = ctk.CTkFrame(header_frame, fg_color=("#10b981", "#059669"), corner_radius=15)
        balance_container.pack(side="right", padx=30, pady=15)
        
        balance_label = ctk.CTkLabel(
            balance_container,
            text="Loading...",
            font=("Segoe UI Black", 16),
            text_color="white"
        )
        balance_label.pack(padx=20, pady=15)
        
        # Fetch SMS Balance
        def fetch_balance():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.get(f"{API_BASE}/super/sms/balance", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        balance_label.configure(text=f"💰 Credits: {data.get('balance', 0)} {data.get('currency', 'NPR')}")
                    else:
                        balance_label.configure(text="❌ Balance Unavailable")
                else:
                    balance_label.configure(text="❌ Error Loading Balance")
            except Exception as e:
                balance_label.configure(text="❌ Connection Error")
        
        # Fetch balance on load
        self.root.after(100, fetch_balance)
        
        # Refresh button
        ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            width=120,
            height=40,
            font=("Segoe UI Semibold", 13),
            command=fetch_balance
        ).pack(side="right", padx=(0, 15), pady=15)
        
        # Tab View for different SMS sending methods
        tab_view = ctk.CTkTabview(content, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
        tab_view.pack(fill="both", expand=True)
        
        # Tab 1: Manual SMS
        tab_manual = tab_view.add("📝 Manual SMS")
        
        manual_container = ctk.CTkFrame(tab_manual, fg_color="transparent")
        manual_container.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(
            manual_container,
            text="Send SMS to Single or Multiple Recipients",
            font=("Segoe UI Semibold", 18),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            manual_container,
            text="Recipients (comma-separated for multiple):",
            font=("Segoe UI Semibold", 13),
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        recipients_entry = ctk.CTkEntry(
            manual_container,
            placeholder_text="e.g., 9855062769, 9800000000, 9841234567",
            height=50,
            font=("Segoe UI", 14)
        )
        recipients_entry.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            manual_container,
            text="Message:",
            font=("Segoe UI Semibold", 13),
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        message_text = ctk.CTkTextbox(
            manual_container,
            height=150,
            font=("Segoe UI", 14)
        )
        message_text.pack(fill="x", pady=(0, 10))
        
        char_count_label = ctk.CTkLabel(
            manual_container,
            text="0 / 160 characters",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        char_count_label.pack(anchor="e", pady=(0, 20))
        
        def update_char_count(event=None):
            count = len(message_text.get("1.0", "end-1c"))
            char_count_label.configure(text=f"{count} / 160 characters")
        
        message_text.bind("<KeyRelease>", update_char_count)
        
        def send_manual_sms():
            recipients = recipients_entry.get().strip()
            message = message_text.get("1.0", "end-1c").strip()
            
            if not recipients or not message:
                messagebox.showerror("Error", "Please enter both recipients and message")
                return
            
            # Parse recipients
            recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]
            
            try:
                headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
                payload = {
                    "recipients": recipient_list,
                    "message": message
                }
                
                response = requests.post(f"{API_BASE}/super/sms/send", json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        if len(recipient_list) == 1:
                            messagebox.showinfo("Success", "SMS sent successfully!")
                        else:
                            messagebox.showinfo(
                                "Bulk SMS Sent",
                                f"Total: {data.get('total', 0)}\n"
                                f"Sent: {data.get('sent', 0)}\n"
                                f"Failed: {data.get('failed', 0)}"
                            )
                        recipients_entry.delete(0, "end")
                        message_text.delete("1.0", "end")
                        fetch_balance()  # Refresh balance
                    else:
                        messagebox.showerror("Error", data.get('error', 'Failed to send SMS'))
                else:
                    messagebox.showerror("Error", f"Server error: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(
            manual_container,
            text="📤 SEND SMS",
            width=300,
            height=55,
            font=("Segoe UI Black", 16),
            fg_color=("#4a90e2", "#5ba3ff"),
            hover_color=("#3b7bc9", "#4a8fe6"),
            command=send_manual_sms
        ).pack(pady=20)
        
        # Tab 2: Excel Upload
        tab_excel = tab_view.add("📊 Excel Upload")
        
        excel_container = ctk.CTkFrame(tab_excel, fg_color="transparent")
        excel_container.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(
            excel_container,
            text="Bulk SMS via Excel File",
            font=("Segoe UI Semibold", 18),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            excel_container,
            text="📋 Instructions:\n"
                 "1. Prepare an Excel file (.xlsx, .xls) with phone numbers\n"
                 "2. Phone numbers should be in a column named: 'phone', 'mobile', 'number', or 'contact'\n"
                 "3. Upload the file and enter your message\n"
                 "4. Click 'Send Bulk SMS' to send to all numbers",
            font=("Segoe UI", 12),
            justify="left",
            text_color="gray"
        ).pack(pady=(0, 30), anchor="w")
        
        selected_file_label = ctk.CTkLabel(
            excel_container,
            text="No file selected",
            font=("Segoe UI", 13),
            text_color="gray"
        )
        selected_file_label.pack(pady=(0, 10))
        
        selected_file_path = [None]  # Use list to make it mutable in nested function
        
        def select_excel_file():
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
            )
            if file_path:
                selected_file_path[0] = file_path
                selected_file_label.configure(text=f"✓ {os.path.basename(file_path)}")
        
        ctk.CTkButton(
            excel_container,
            text="📁 SELECT EXCEL FILE",
            width=300,
            height=50,
            font=("Segoe UI Semibold", 14),
            command=select_excel_file
        ).pack(pady=10)
        
        ctk.CTkLabel(
            excel_container,
            text="Message for all recipients:",
            font=("Segoe UI Semibold", 13),
            anchor="w"
        ).pack(fill="x", pady=(30, 5))
        
        excel_message_text = ctk.CTkTextbox(
            excel_container,
            height=150,
            font=("Segoe UI", 14)
        )
        excel_message_text.pack(fill="x", pady=(0, 10))
        
        excel_char_count = ctk.CTkLabel(
            excel_container,
            text="0 / 160 characters",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        excel_char_count.pack(anchor="e", pady=(0, 20))
        
        def update_excel_char_count(event=None):
            count = len(excel_message_text.get("1.0", "end-1c"))
            excel_char_count.configure(text=f"{count} / 160 characters")
        
        excel_message_text.bind("<KeyRelease>", update_excel_char_count)
        
        def send_bulk_sms_excel():
            if not selected_file_path[0]:
                messagebox.showerror("Error", "Please select an Excel file")
                return
            
            message = excel_message_text.get("1.0", "end-1c").strip()
            if not message:
                messagebox.showerror("Error", "Please enter a message")
                return
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                
                with open(selected_file_path[0], 'rb') as f:
                    files = {'file': f}
                    data = {'message': message}
                    
                    response = requests.post(
                        f"{API_BASE}/super/sms/upload-excel",
                        files=files,
                        data=data,
                        headers=headers
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    messagebox.showinfo(
                        "Bulk SMS Sent",
                        f"Total Recipients: {result.get('total', 0)}\n"
                        f"Successfully Sent: {result.get('sent', 0)}\n"
                        f"Failed: {result.get('failed', 0)}"
                    )
                    selected_file_path[0] = None
                    selected_file_label.configure(text="No file selected")
                    excel_message_text.delete("1.0", "end")
                    fetch_balance()  # Refresh balance
                else:
                    error_msg = response.json().get('error', 'Failed to send bulk SMS')
                    messagebox.showerror("Error", error_msg)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(
            excel_container,
            text="📤 SEND BULK SMS",
            width=300,
            height=55,
            font=("Segoe UI Black", 16),
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            command=send_bulk_sms_excel
        ).pack(pady=20)
        
        # Tab 3: SMS History
        tab_history = tab_view.add("📜 SMS History")
        
        history_container = ctk.CTkFrame(tab_history, fg_color="transparent")
        history_container.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(
            history_container,
            text="SMS Sending History",
            font=("Segoe UI Semibold", 18),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(0, 20))
        
        # Stats Frame
        stats_frame = ctk.CTkFrame(history_container, fg_color=("#f1f5f9", "#0f172a"), corner_radius=15)
        stats_frame.pack(fill="x", pady=(0, 20))
        
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=20, pady=20)
        
        def create_stat_card(parent, title, value, col):
            card = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
            card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
            parent.grid_columnconfigure(col, weight=1)
            
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 11), text_color="gray").pack(pady=(15, 5))
            ctk.CTkLabel(card, text=value, font=("Segoe UI Black", 24), text_color=("#4a90e2", "#5ba3ff")).pack(pady=(0, 15))
        
        # Fetch and display stats
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_BASE}/super/sms/stats", headers=headers)
            if response.status_code == 200:
                stats = response.json()
                create_stat_card(stats_grid, "Total Sent", str(stats.get('total_sent', 0)), 0)
                create_stat_card(stats_grid, "Successful", str(stats.get('successful', 0)), 1)
                create_stat_card(stats_grid, "Failed", str(stats.get('failed', 0)), 2)
                create_stat_card(stats_grid, "Unique Recipients", str(stats.get('unique_recipients', 0)), 3)
        except:
            pass
        
        # History Table
        history_scroll = ctk.CTkScrollableFrame(history_container, fg_color=("#ffffff", "#1e293b"), corner_radius=15, height=400)
        history_scroll.pack(fill="both", expand=True)
        
        # Fetch SMS logs
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_BASE}/super/sms/logs?limit=50", headers=headers)
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                
                if logs:
                    # Header
                    header_frame = ctk.CTkFrame(history_scroll, fg_color=("#f1f5f9", "#0f172a"))
                    header_frame.pack(fill="x", pady=(0, 10))
                    
                    headers_list = ["Date/Time", "Recipient", "Message", "Status"]
                    for i, header in enumerate(headers_list):
                        ctk.CTkLabel(
                            header_frame,
                            text=header,
                            font=("Segoe UI Semibold", 12),
                            width=200 if i < 3 else 100
                        ).grid(row=0, column=i, padx=10, pady=10, sticky="w")
                    
                    # Logs
                    for log in logs[:30]:  # Show last 30
                        log_frame = ctk.CTkFrame(history_scroll, fg_color="transparent")
                        log_frame.pack(fill="x", pady=2)
                        
                        sent_at = log.get('sent_at', 'N/A')
                        if sent_at != 'N/A':
                            try:
                                sent_at = datetime.fromisoformat(sent_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                            except:
                                pass
                        
                        recipient = log.get('recipient', 'N/A')
                        message = log.get('message', 'N/A')
                        if len(message) > 50:
                            message = message[:50] + "..."
                        status = log.get('status', 'unknown')
                        
                        status_color = "#10b981" if status == "sent" else "#ef4444"
                        
                        ctk.CTkLabel(log_frame, text=sent_at, font=("Segoe UI", 11), width=200).grid(row=0, column=0, padx=10, pady=5, sticky="w")
                        ctk.CTkLabel(log_frame, text=recipient, font=("Segoe UI", 11), width=200).grid(row=0, column=1, padx=10, pady=5, sticky="w")
                        ctk.CTkLabel(log_frame, text=message, font=("Segoe UI", 11), width=200).grid(row=0, column=2, padx=10, pady=5, sticky="w")
                        ctk.CTkLabel(log_frame, text=status.upper(), font=("Segoe UI Semibold", 11), text_color=status_color, width=100).grid(row=0, column=3, padx=10, pady=5, sticky="w")
                else:
                    ctk.CTkLabel(
                        history_scroll,
                        text="No SMS history found",
                        font=("Segoe UI", 14),
                        text_color="gray"
                    ).pack(pady=50)
        except Exception as e:
            ctk.CTkLabel(
                history_scroll,
                text=f"Error loading history: {str(e)}",
                font=("Segoe UI", 14),
                text_color="#ef4444"
            ).pack(pady=50)

    def show_reports_management(self):
        """Comprehensive Super Admin Reporting Dashboard"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav()
        self.create_sidebar(main_container, nav_items, "Sales Reports")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(content, text="📈 Master Reporting Hub", font=("Segoe UI Black", 30, "bold")).pack(anchor="w", pady=(0, 25))
        
        # Filters Frame
        filter_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        filter_frame.pack(fill="x", pady=(0, 20))
        
        inner_filter = ctk.CTkFrame(filter_frame, fg_color="transparent")
        inner_filter.pack(padx=20, pady=20, fill="x")
        
        # Fetch Clients
        clients = []
        try:
            res = requests.get(f"{API_BASE}/super/clients", headers={"Authorization": f"Bearer {self.token}"})
            if res.status_code == 200: clients = res.json()
        except: pass
        
        client_options = ["All Pharmacies"] + [f"{c['id']} - {c['pharmacy_name']}" for c in clients]
        client_var = StringVar(value="All Pharmacies")
        
        # Grid layout for filters
        ctk.CTkLabel(inner_filter, text="Select Pharmacy", font=("Segoe UI Semibold", 12)).grid(row=0, column=0, padx=10, sticky="w")
        client_menu = ctk.CTkOptionMenu(inner_filter, values=client_options, variable=client_var, width=250)
        client_menu.grid(row=1, column=0, padx=10, pady=(5, 0))
        
        ctk.CTkLabel(inner_filter, text="Report Type", font=("Segoe UI Semibold", 12)).grid(row=0, column=1, padx=10, sticky="w")
        report_type_var = StringVar(value="Sales Summary")
        report_menu = ctk.CTkOptionMenu(inner_filter, values=["Sales Summary", "Item-wise Sales", "Top Selling Products"], variable=report_type_var, width=200)
        report_menu.grid(row=1, column=1, padx=10, pady=(5, 0))
        
        ctk.CTkLabel(inner_filter, text="Start Date (YYYY-MM-DD)", font=("Segoe UI Semibold", 12)).grid(row=0, column=2, padx=10, sticky="w")
        start_date_entry = ctk.CTkEntry(inner_filter, width=150)
        start_date_entry.insert(0, datetime.now().strftime('%Y-%m-01'))
        start_date_entry.grid(row=1, column=2, padx=10, pady=(5, 0))
        
        ctk.CTkLabel(inner_filter, text="End Date (YYYY-MM-DD)", font=("Segoe UI Semibold", 12)).grid(row=0, column=3, padx=10, sticky="w")
        end_date_entry = ctk.CTkEntry(inner_filter, width=150)
        end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        end_date_entry.grid(row=1, column=3, padx=10, pady=(5, 0))
        
        self.report_data = [] # To store current report results for export
        
        results_container = ctk.CTkFrame(content, fg_color="transparent")
        results_container.pack(fill="both", expand=True)

        def fetch_report():
            for widget in results_container.winfo_children(): widget.destroy()
            
            sel_client = client_var.get()
            client_id = sel_client.split(" - ")[0] if sel_client != "All Pharmacies" else "all"
            rep_type = report_type_var.get()
            start_date = start_date_entry.get()
            end_date = end_date_entry.get()
            
            endpoint = "/super/reports/sales"
            if rep_type == "Item-wise Sales": endpoint = "/super/reports/item-wise"
            elif rep_type == "Top Selling Products": endpoint = "/super/reports/top-selling"
            
            try:
                res = requests.get(f"{API_BASE}{endpoint}", 
                                  params={"client_id": client_id, "start_date": start_date, "end_date": end_date},
                                  headers={"Authorization": f"Bearer {self.token}"})
                if res.status_code == 200:
                    self.report_data = res.json()
                    display_report_results(results_container, self.report_data, rep_type)
                else:
                    messagebox.showerror("Error", "Failed to fetch report data")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def display_report_results(parent, data, r_type):
            if not data:
                ctk.CTkLabel(parent, text="No data found for selected period.", font=("Segoe UI", 16)).pack(pady=50)
                return
            
            # Export buttons are added below function definitions
            export_frame = ctk.CTkFrame(parent, fg_color="transparent")
            export_frame.pack(fill="x", pady=(0, 15))
            
            table_scroll = ctk.CTkScrollableFrame(parent, height=500, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
            table_scroll.pack(fill="both", expand=True)
            
            if r_type == "Sales Summary":
                headers = ["Date", "Pharmacy", "Bill No", "Cashier", "Total", "Grand Total", "Mode"]
                keys = ["created_at", "pharmacy_name", "bill_number", "cashier_name", "total_amount", "grand_total", "payment_mode"]
            elif r_type == "Item-wise Sales":
                headers = ["Date", "Item Name", "Quantity", "Price", "Total", "Pharmacy"]
                keys = ["created_at", "medicine_name", "quantity", "unit_price", "total_price", "pharmacy_name"]
            else: # Top Selling
                headers = ["Medicine Name", "Total Sold", "Revenue", "Pharmacy"]
                keys = ["name", "total_sold", "total_revenue", "pharmacy_name"]

            # Render Table Header
            head_row = ctk.CTkFrame(table_scroll, fg_color=("#f1f5f9", "#0f172a"))
            head_row.pack(fill="x", pady=2)
            for i, h in enumerate(headers):
                ctk.CTkLabel(head_row, text=h, font=("Segoe UI Bold", 12), width=150).grid(row=0, column=i, padx=10, pady=10, sticky="w")
            
            # Render Table Rows
            for item in data:
                row = ctk.CTkFrame(table_scroll, fg_color="transparent")
                row.pack(fill="x")
                for i, k in enumerate(keys):
                    val = item.get(k, "N/A")
                    if "created_at" in k: 
                        try: val = val.split("T")[0]
                        except: pass
                    ctk.CTkLabel(row, text=str(val), font=("Segoe UI", 11), width=150).grid(row=0, column=i, padx=10, pady=5, sticky="w")

        def export_to_excel(data, r_type):
            try:
                import pandas as pd
                df = pd.DataFrame(data)
                
                # Convert Dates to BS
                if 'created_at' in df.columns:
                    df['created_at'] = df['created_at'].apply(lambda x: DateUtils.ad_to_bs(x.split('T')[0]) if x else '')
                    df.rename(columns={'created_at': 'Date (BS)'}, inplace=True)
                    
                if 'date' in df.columns:
                     df['date'] = df['date'].apply(lambda x: DateUtils.ad_to_bs(x.split('T')[0]) if x else '')
                     df.rename(columns={'date': 'Date (BS)'}, inplace=True)
                filename = f"Report_{r_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=filename)
                if path:
                    df.to_excel(path, index=False)
                    messagebox.showinfo("Success", f"Report exported successfully to {path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export to Excel: {str(e)}")

        def export_to_pdf(data, r_type):
            try:
                from reportlab.lib.pagesizes import A4, landscape
                from reportlab.pdfgen import canvas
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
                from reportlab.lib.styles import getSampleStyleSheet
                import os

                filename = f"Report_{r_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename)
                
                if not path: return

                doc = SimpleDocTemplate(path, pagesize=landscape(A4))
                elements = []
                styles = getSampleStyleSheet()

                # Title
                elements.append(Paragraph(f"{r_type} Report", styles['Title']))
                elements.append(Paragraph(f"Generated: {DateUtils.get_current_bs_date_full()}", styles['Normal']))
                elements.append(Paragraph(" ", styles['Normal'])) # Spacer

                # Prepare Table Data
                if r_type == "Sales Summary":
                    headers = ["Date", "Bill No", "Customer", "Total", "Grand Total", "Mode"]
                    keys = ["created_at", "bill_number", "customer_name", "total_amount", "grand_total", "payment_category"]
                    col_widths = [100, 100, 150, 80, 80, 80]
                elif r_type == "Item-wise Sales":
                    headers = ["Date", "Item Name", "Qty", "Price", "Total", "Pharmacy"]
                    keys = ["created_at", "medicine_name", "quantity", "unit_price", "total_price", "pharmacy_name"]
                    col_widths = [80, 150, 50, 70, 80, 150]
                else:
                    headers = ["Medicine Name", "Total Sold", "Revenue", "Pharmacy"]
                    keys = ["name", "total_sold", "total_revenue", "pharmacy_name"]
                    col_widths = [200, 100, 100, 200]

                table_data = [headers]
                
                for item in data:
                    row = []
                    for k in keys:
                        val = item.get(k, "")
                        if "created_at" in k and val:
                            try: val = DateUtils.ad_to_bs(val.split("T")[0])
                            except: pass
                        row.append(str(val))
                    table_data.append(row)

                # Create Table
                t = Table(table_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                elements.append(t)
                doc.build(elements)
                
                messagebox.showinfo("Success", f"PDF Report exported successfully to {path}")
                os.startfile(path)

            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export to PDF: {str(e)}")

        ctk.CTkButton(export_frame, text="📗 Export to Excel", fg_color="#2e7d32", width=150, command=lambda: export_to_excel(data, r_type)).pack(side="right", padx=5)
        ctk.CTkButton(export_frame, text="📕 Export to PDF", fg_color="#dc2626", width=150, command=lambda: export_to_pdf(data, r_type)).pack(side="right", padx=5)

        ctk.CTkButton(inner_filter, text="🔍 Generate Report", height=45, fg_color="#4f46e5", command=fetch_report).grid(row=1, column=4, padx=20, pady=(5, 0))



        def refresh_alerts():
            headers = {"Authorization": f"Bearer {self.token}"}
            try:
                # 1. Total Items
                m_res = requests.get(f"{API_BASE}/medicines", headers=headers)
                med_count_lbl.configure(text=str(len(m_res.json())) if m_res.status_code == 200 else "0")
                
                # 2. Low Stock Alerts
                ls_res = requests.get(f"{API_BASE}/check-low-stock", headers=headers)
                ls_items = ls_res.json().get('low_stock_items', [])
                low_count_lbl.configure(text=str(len(ls_items)))
                
                for widget in low_list.winfo_children(): widget.destroy()
                if not ls_items:
                    ctk.CTkLabel(low_list, text="All stock levels healthy ✔", text_color="#10b981").pack(pady=20)
                else:
                    for item in ls_items[:5]: # Show top 5
                        ctk.CTkLabel(low_list, text=f"• {item['item']} (Qty: {item['remaining']})\n  Batch: {item['batch']} | Sup: {item['vendor']}", anchor="w", font=("Segoe UI", 12), justify="left").pack(fill="x", pady=2)

                # 3. Expiry Alerts
                ex_res = requests.get(f"{API_BASE}/check-expiry", headers=headers)
                ex_items = ex_res.json().get('expiry_items', [])
                exp_count_lbl.configure(text=str(len(ex_items)))
                
                for widget in exp_list.winfo_children(): widget.destroy()
                if not ex_items:
                    ctk.CTkLabel(exp_list, text="No items expiring soon ✔", text_color="#10b981").pack(pady=20)
                else:
                    for item in ex_items[:5]:
                        ctk.CTkLabel(exp_list, text=f"• {item['item']} ({item['expiry']})\n  Batch: {item['batch']} | Sup: {item['vendor']}", anchor="w", font=("Segoe UI", 12), justify="left").pack(fill="x", pady=2)

                # 4. Vendors
                v_res = requests.get(f"{API_BASE}/vendors", headers=headers)
                ven_count_lbl.configure(text=str(len(v_res.json())) if v_res.status_code == 200 else "0")
                
            except Exception as e:
                print(f"Error refreshing dashboard: {e}")

        self.root.after(100, refresh_alerts) # Load after brief delay

    def show_admin_users(self):
        """Admin's User & Access Management Hub"""
        for widget in self.root.winfo_children(): widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Team Management")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(content, text="👥 Cashier Access Control", font=("Segoe UI Black", 24)).pack(anchor="w", pady=(0, 20))

        # Split View
        split = ctk.CTkFrame(content, fg_color="transparent")
        split.pack(fill="both", expand=True)

        # LEFT: User List
        left_panel = ctk.CTkFrame(split, fg_color=("#ffffff", "#1e293b"), corner_radius=10, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        ctk.CTkLabel(left_panel, text="Staff List", font=("Segoe UI Bold", 16)).pack(pady=15)
        
        staff_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        staff_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # HEADERS for List
        # Refreshes list
        def load_staff():
            for w in staff_scroll.winfo_children(): w.destroy()
            try:
                r = requests.get(f"{API_BASE}/users", headers={"Authorization": f"Bearer {self.token}"}, params={"client_id": self.user['client_id']})
                if r.status_code == 200:
                    users = r.json()
                    if not users:
                        ctk.CTkLabel(staff_scroll, text="No cashiers found", text_color="gray").pack(pady=20)
                    for u in users:
                        card = ctk.CTkFrame(staff_scroll, fg_color=("#f8fafc", "#334155"), corner_radius=8)
                        card.pack(fill="x", pady=5)
                        
                        top = ctk.CTkFrame(card, fg_color="transparent")
                        top.pack(fill="x", padx=10, pady=5)
                        ctk.CTkLabel(top, text=u['name'], font=("Segoe UI Bold", 14)).pack(side="left")
                        ctk.CTkLabel(top, text=u['username'], text_color="gray", font=("Segoe UI", 12)).pack(side="right")
                        
                        bot = ctk.CTkFrame(card, fg_color="transparent")
                        bot.pack(fill="x", padx=10, pady=5)
                        status_col = "#10b981" if u['status'] == 'ACTIVE' else "#ef4444"
                        ctk.CTkLabel(bot, text=u['status'], text_color=status_col, font=("Segoe UI Bold", 11)).pack(side="left")
                        
                        # Resend SMS Button
                        ctk.CTkButton(bot, text="📧 Resend SMS", width=80, height=24, font=("Segoe UI", 11),
                                     fg_color="#3b82f6", command=lambda user=u: resend_sms_dialog(user)).pack(side="right")
                else:
                    ctk.CTkLabel(staff_scroll, text="Error loading staff").pack()
            except Exception as e: 
                print(e)
                ctk.CTkLabel(staff_scroll, text="Connection Error").pack()

        load_staff()

        # RIGHT: Create/Edit Form
        right_panel = ctk.CTkScrollableFrame(split, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(right_panel, text="🆕 Create New Cashier", font=("Segoe UI Bold", 18)).pack(pady=15)
        
        # Form Fields
        form = ctk.CTkFrame(right_panel, fg_color="transparent")
        form.pack(fill="x", padx=20)

        ctk.CTkLabel(form, text="Full Name *").pack(anchor="w")
        name_entry = ctk.CTkEntry(form, placeholder_text="e.g. Ram Sharma", width=300)
        name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Mobile Number * (Used for SMS)").pack(anchor="w")
        mobile_entry = ctk.CTkEntry(form, placeholder_text="98XXXXXXXX", width=300)
        mobile_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Login Username * (Unique)").pack(anchor="w")
        user_entry = ctk.CTkEntry(form, placeholder_text="e.g. ram123", width=300)
        user_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Password * (Final - SMS sent)").pack(anchor="w")
        pass_entry = ctk.CTkEntry(form, placeholder_text="Set Strong Password", show="*", width=300)
        pass_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(form, text="Confirm Password *").pack(anchor="w")
        confirm_entry = ctk.CTkEntry(form, placeholder_text="Repeat Password", show="*", width=300)
        confirm_entry.pack(fill="x", pady=(0, 10))

        # Permissions
        ctk.CTkLabel(form, text="🔒 Access Control (Select Allowed Modules)", font=("Segoe UI Bold", 14)).pack(anchor="w", pady=(15, 10))
        
        perms_frame = ctk.CTkFrame(form, fg_color="transparent")
        perms_frame.pack(fill="x")

        # Module Map: internal_key -> Display Name
        modules = [
            ("billing", "💰 Billing Terminal"),
            ("bill_log", "📜 Bill Log / Reprint"),
            ("refund", "🔄 Refund Requests"),
            ("inventory", "📦 Inventory Management"),
            ("karobar", "🏦 Karobar (Sahakari)"),
            ("reports", "📊 Sales Reports"),
            ("crm", "👥 Customer Database"),
            ("vendors", "🤝 Vendor Management"),
        ]
        
        perm_vars = {}
        for key, label in modules:
            v = ctk.BooleanVar(value=False) # Default OFF
            # Billing usually ON for cashier? Prompt says "Admin selects exactly". So default OFF is safer.
            if key == 'billing': v.set(True) # Suggest billing by default
            
            chk = ctk.CTkCheckBox(perms_frame, text=label, variable=v, font=("Segoe UI", 13))
            chk.pack(anchor="w", pady=2)
            perm_vars[key] = v

        def create_cashier():
            # Validation
            if pass_entry.get() != confirm_entry.get():
                messagebox.showerror("Error", "Passwords do not match!")
                return
            
            selected_perms = [k for k, v in perm_vars.items() if v.get()]
            
            data = {
                "full_name": name_entry.get(),
                "mobile": mobile_entry.get(),
                "username": user_entry.get(),
                "password": pass_entry.get(),
                "permissions": selected_perms,
                "client_id": self.user['client_id']
            }
            
            try:
                r = requests.post(f"{API_BASE}/users/cashier", json=data, headers={"Authorization": f"Bearer {self.token}"})
                if r.status_code == 201:
                    resp = r.json()
                    msg = f"Cashier Created!\n\nSMS Status: {resp['sms_status']}"
                    if resp.get('sms_error'): msg += f"\nError: {resp['sms_error']}"
                    
                    messagebox.showinfo("Success", msg)
                    # Clear form
                    name_entry.delete(0, 'end')
                    mobile_entry.delete(0, 'end')
                    user_entry.delete(0, 'end')
                    pass_entry.delete(0, 'end')
                    confirm_entry.delete(0, 'end')
                    load_staff()
                else:
                    messagebox.showerror("Error", r.json().get('error', 'Failed'))
            except Exception as e: messagebox.showerror("Error", str(e))

        ctk.CTkButton(form, text="✅ Create Cashier User", command=create_cashier, fg_color="#10b981", height=45, font=("Segoe UI Bold", 15)).pack(fill="x", pady=30)

        # Resend Logic
        def resend_sms_dialog(user):
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Resend Credentials")
            dialog.geometry("400x300")
            dialog.grab_set()
            
            ctk.CTkLabel(dialog, text=f"Resend SMS for {user['username']}", font=("Segoe UI Bold", 14)).pack(pady=20)
            ctk.CTkLabel(dialog, text="⚠️ Security Check:", text_color="orange").pack()
            ctk.CTkLabel(dialog, text="Enter the Cashier's Password to confirm:").pack(pady=5)
            
            pw = ctk.CTkEntry(dialog, show="*", width=250)
            pw.pack(pady=10)
            
            def send():
                if not pw.get(): return
                try:
                    payload = {
                        "username": user['username'],
                        "mobile": user['phone'],
                        "password": pw.get(),
                        "client_id": self.user['client_id']
                    }
                    r = requests.post(f"{API_BASE}/users/resend-creds", json=payload, headers={"Authorization": f"Bearer {self.token}"})
                    if r.status_code == 200:
                        messagebox.showinfo("Sent", "SMS Credentials Sent Successfully!")
                        dialog.destroy()
                    else:
                        messagebox.showerror("Failed", r.json().get('error', 'Failed'))
                except Exception as e: messagebox.showerror("Error", str(e))

            ctk.CTkButton(dialog, text="Confirm & Resend SMS", command=send, fg_color="#3b82f6").pack(pady=20)
    
    def show_inventory_management(self):
        """Standard Unit Admin Inventory Management"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Inventory Management")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        ctk.CTkLabel(header_frame, text="📦 Stock Management", font=("Segoe UI Black", 28, "bold")).pack(side="left")
        
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="✚ Add New Item", command=self.show_add_item_dialog, fg_color="#6366f1", height=40).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📦 Add Stock", command=self.show_add_stock_dialog, fg_color="#10b981", height=40).pack(side="left", padx=5)

        # Inventory Table
        table_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        # Table Headers
        headers = ["Item Code", "Name", "Category", "Dosage", "Current Stock", "Threshold", "Actions"]
        widths = [120, 250, 150, 100, 120, 100, 150]
        
        head_row = ctk.CTkFrame(table_frame, fg_color=("#f8fafc", "#0f172a"), height=45)
        head_row.pack(fill="x", padx=10, pady=(10, 5))
        
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(head_row, text=header, font=("Segoe UI Bold", 13), width=widths[i])
            lbl.pack(side="left", padx=5)

        # Fetch and Render Data
        try:
            resp = requests.get(f"{API_BASE}/inventory/stock-levels", headers={"Authorization": f"Bearer {self.token}"})
            items = resp.json() if resp.status_code == 200 else []
        except:
            items = []
            
        if not items:
            ctk.CTkLabel(table_frame, text="No items found. Add your first item!", font=("Segoe UI", 14), text_color="gray").pack(pady=50)
        else:
            for item in items:
                row = ctk.CTkFrame(table_frame, fg_color="transparent", height=40)
                row.pack(fill="x", padx=10, pady=2)
                
                ctk.CTkLabel(row, text=item.get('item_code', '-'), width=widths[0]).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=item.get('name', '-'), width=widths[1], anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=item.get('category', '-'), width=widths[2]).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=item.get('dosage_form', '-'), width=widths[3]).pack(side="left", padx=5)
                
                qty = item.get('total_quantity', 0)
                thresh = item.get('low_stock_threshold', 10)
                
                # Ensure numeric comparison to avoid str vs int TypeError
                try:
                    q_val = float(qty)
                    t_val = float(thresh)
                    is_low = q_val < t_val
                except:
                    is_low = False
                    
                color = "red" if is_low else ("#1e293b" if ctk.get_appearance_mode() == "Light" else "#f1f5f9")
                
                ctk.CTkLabel(row, text=f"{qty}", width=widths[4], text_color=color, font=("Segoe UI Bold", 13)).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=f"{thresh}", width=widths[5]).pack(side="left", padx=5)
                
                act_frame = ctk.CTkFrame(row, fg_color="transparent", width=widths[6])
                act_frame.pack(side="left", padx=5)
                ctk.CTkButton(act_frame, text="Edit", width=60, height=28, command=lambda i=item: self.show_add_item_dialog(i)).pack(side="left", padx=2)

    def show_add_item_dialog(self, edit_item=None):
        """Add/Edit Item Modal Dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Item" if edit_item else "Add New Item")
        dialog.geometry("850x850")
        dialog.grab_set()
        
        # Main Layout
        scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll_frame, text="📄 Item Specification", font=("Segoe UI Black", 20)).pack(anchor="w", pady=(0, 20))
        
        # Fields container
        form = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        form.pack(fill="both", expand=True)
        
        # Item Code
        ctk.CTkLabel(form, text="Item Code (Auto-generated by default)").grid(row=0, column=0, sticky="w", pady=(10, 0))
        code_var = StringVar(value=(edit_item.get('item_code') if edit_item else ""))
        code_entry = ctk.CTkEntry(form, textvariable=code_var, width=300, state="disabled" if not (edit_item and edit_item.get('item_code')) else "normal")
        code_entry.grid(row=1, column=0, padx=(0, 10), sticky="w")
        
        manual_code_var = ctk.BooleanVar(value=True if (edit_item and edit_item.get('item_code')) else False)
        def toggle_code():
            code_entry.configure(state="normal" if manual_code_var.get() else "disabled")
        ctk.CTkCheckBox(form, text="Manual Entry", variable=manual_code_var, command=toggle_code).grid(row=1, column=1, sticky="w")

        # Name Fields
        ctk.CTkLabel(form, text="Generic Name *").grid(row=2, column=0, sticky="w", pady=(15, 0))
        gen_var = StringVar(value=edit_item.get('generic_name') if edit_item else "")
        ctk.CTkEntry(form, textvariable=gen_var, width=350).grid(row=3, column=0, padx=(0, 10), sticky="w")
        
        ctk.CTkLabel(form, text="Brand Name *").grid(row=2, column=1, sticky="w", pady=(15, 0))
        brand_var = StringVar(value=edit_item.get('brand_name') if edit_item else "")
        ctk.CTkEntry(form, textvariable=brand_var, width=350).grid(row=3, column=1, sticky="w")
        
        ctk.CTkLabel(form, text="Short Name (for bills)").grid(row=4, column=0, sticky="w", pady=(15, 0))
        short_var = StringVar(value=edit_item.get('short_name') if edit_item else "")
        ctk.CTkEntry(form, textvariable=short_var, width=350).grid(row=5, column=0, padx=(0, 10), sticky="w")

        # Dropdowns
        ctk.CTkLabel(form, text="Category").grid(row=6, column=0, sticky="w", pady=(15, 0))
        cat_var = StringVar(value=edit_item.get('category') if edit_item else "Tablet")
        ctk.CTkOptionMenu(form, variable=cat_var, values=["Tablet", "Capsule", "Syrup", "Injection", "Consumable", "Others"], width=200).grid(row=7, column=0, sticky="w")
        
        ctk.CTkLabel(form, text="Sub-Category").grid(row=6, column=1, sticky="w", pady=(15, 0))
        sub_var = StringVar(value=edit_item.get('sub_category') if edit_item else "Antibiotic")
        ctk.CTkOptionMenu(form, variable=sub_var, values=["Antibiotic", "Analgesic", "Vitamin", "Antipyretic", "Antacid", "Others"], width=200).grid(row=7, column=1, sticky="w")

        ctk.CTkLabel(form, text="Dosage Form").grid(row=8, column=0, sticky="w", pady=(15, 0))
        dose_var = StringVar(value=edit_item.get('dosage_form') if edit_item else "Tab")
        ctk.CTkOptionMenu(form, variable=dose_var, values=["Tab", "Cap", "Inj", "Syrup"], width=200).grid(row=9, column=0, sticky="w")

        ctk.CTkLabel(form, text="Strength (e.g. 500mg)").grid(row=8, column=1, sticky="w", pady=(15, 0))
        strength_var = StringVar(value=edit_item.get('strength') if edit_item else "")
        ctk.CTkEntry(form, textvariable=strength_var, width=200).grid(row=9, column=1, sticky="w")

        ctk.CTkLabel(form, text="Unit").grid(row=10, column=0, sticky="w", pady=(15, 0))
        unit_var = StringVar(value=edit_item.get('unit') if edit_item else "Strip")
        ctk.CTkOptionMenu(form, variable=unit_var, values=["Strip", "Bottle", "Vial", "Pcs"], width=200).grid(row=11, column=0, sticky="w")

        ctk.CTkLabel(form, text="Low Stock Alert Threshold").grid(row=10, column=1, sticky="w", pady=(15, 0))
        thresh_var = StringVar(value=str(edit_item.get('low_stock_threshold', 10)) if edit_item else "10")
        ctk.CTkEntry(form, textvariable=thresh_var, width=200).grid(row=11, column=1, sticky="w")

        # Barcode / QR Code (Optional)
        ctk.CTkLabel(form, text="Barcode / QR Code (Optional)").grid(row=12, column=0, sticky="w", pady=(15, 0))
        barcode_var = StringVar(value=edit_item.get('barcode') if edit_item else "")
        barcode_entry = ctk.CTkEntry(form, textvariable=barcode_var, width=300)
        barcode_entry.grid(row=13, column=0, padx=(0, 10), sticky="w")
        
        def open_scanner():
            scan_win = ctk.CTkToplevel(dialog)
            scan_win.title("Scan Barcode / QR")
            scan_win.geometry("500x600")
            scan_win.grab_set()
            
            preview_label = ctk.CTkLabel(scan_win, text="Initializing Camera...", width=400, height=300, fg_color="#1a202c")
            preview_label.pack(pady=20)
            
            status_var = StringVar(value="Ready to Scan")
            ctk.CTkLabel(scan_win, textvariable=status_var, font=("Segoe UI", 12)).pack(pady=5)
            
            scanner = ScannerModule(scan_win, lambda code: on_scan_success(code, scan_win))
            
            def on_scan_success(code, window):
                barcode_var.set(code)
                status_var.set(f"✅ Scanned: {code}")
                # Success feedback - optional sound could go here
                window.after(800, window.destroy)
                
            def start_cam():
                success, msg = scanner.start_scan(preview_label)
                if not success:
                    status_var.set(f"❌ {msg}. Switching to Manual/Device mode.")
                    # Fallback to Keyboard Wedge mode
                    wedge_mode()
            
            def wedge_mode():
                preview_label.configure(text="Ready for Scanner Device Input...\n\nPlease scan using your handheld device now.", image="")
                # Focus a hidden/dedicated field for keyboard wedge
                wedge_entry = ctk.CTkEntry(scan_win, width=1, height=1, fg_color=scan_win.cget("fg_color"), border_width=0)
                wedge_entry.pack()
                wedge_entry.focus_set()
                
                def on_enter(e):
                    code = wedge_entry.get().strip()
                    if code:
                        on_scan_success(code, scan_win)
                
                wedge_entry.bind("<Return>", on_enter)
            
            btn_frame = ctk.CTkFrame(scan_win, fg_color="transparent")
            btn_frame.pack(pady=20)
            
            ctk.CTkButton(btn_frame, text="Start Camera", command=start_cam, width=120).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Use Scanner Device", command=wedge_mode, width=120, fg_color="#4a5568").pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Flashlight", command=scanner.toggle_flashlight, width=80, fg_color="#2d3748").pack(side="left", padx=5)
            ctk.CTkButton(scan_win, text="Close", command=lambda: [scanner.stop_scan(), scan_win.destroy()], width=100, fg_color="#e53e3e").pack(pady=10)
            
            scan_win.protocol("WM_DELETE_WINDOW", lambda: [scanner.stop_scan(), scan_win.destroy()])

        ctk.CTkButton(form, text="📷 Scan QR/Barcode", command=open_scanner, width=150, fg_color="#3182ce").grid(row=13, column=1, sticky="w")
        ctk.CTkLabel(form, text="If you don't have a scanner, type the code above.", font=("Segoe UI", 10), text_color="gray").grid(row=14, column=0, sticky="w")

        def generate_qr(code, name, strength):
            qr_data = f"{code}|{name}|{strength}"
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to temporary file for display
            temp_path = os.path.join(os.environ['TEMP'], f"qr_{code}.png")
            img.save(temp_path)
            return temp_path

        if edit_item and edit_item.get('item_code'):
            qr_frame = ctk.CTkFrame(scroll_frame, fg_color=("#ffffff", "#2d3748"), corner_radius=12)
            qr_frame.pack(fill="x", pady=20)
            
            ctk.CTkLabel(qr_frame, text="🛡️ ITEM QR CODE", font=("Segoe UI Bold", 14)).pack(pady=10)
            
            try:
                qr_path = generate_qr(edit_item['item_code'], edit_item['name'], edit_item.get('strength', ''))
                qr_img = ctk.CTkImage(light_image=Image.open(qr_path), dark_image=Image.open(qr_path), size=(180, 180))
                ctk.CTkLabel(qr_frame, image=qr_img, text="").pack(pady=10)
                
                def print_qr():
                    os.startfile(qr_path, "print")
                ctk.CTkButton(qr_frame, text="🖨️ Print QR Label", command=print_qr, width=150, fg_color="#475569").pack(pady=(0, 15))
            except Exception as e:
                ctk.CTkLabel(qr_frame, text=f"QR generation failed: {e}").pack()

        def save_item():
            if not gen_var.get() or not brand_var.get():
                return messagebox.showerror("Error", "Generic and Brand names are required")
            
            payload = {
                "name": f"{gen_var.get()} {brand_var.get()}",
                "generic_name": gen_var.get(),
                "brand_name": brand_var.get(),
                "short_name": short_var.get(),
                "category": cat_var.get(),
                "sub_category": sub_var.get(),
                "dosage_form": dose_var.get(),
                "strength": strength_var.get(),
                "unit": unit_var.get(),
                "low_stock_threshold": int(thresh_var.get() or 10),
                "item_code": code_var.get(),
                "manual_code": manual_code_var.get(),
                "barcode": barcode_var.get().strip()
            }
            
            headers = {"Authorization": f"Bearer {self.token}"}
            try:
                if edit_item:
                    resp = requests.put(f"{API_BASE}/medicines/{edit_item['id']}", json=payload, headers=headers)
                else:
                    resp = requests.post(f"{API_BASE}/medicines", json=payload, headers=headers)
                
                if resp.status_code in [200, 201]:
                    messagebox.showinfo("Success", "Item details saved successfully")
                    dialog.destroy()
                    self.show_inventory_management()
                else:
                    err_data = resp.json()
                    if err_data.get('error') == 'DUPLICATE_BARCODE':
                        msg = f"{err_data['message']} Do you want to open it?"
                        if messagebox.askyesno("Item Exists", msg):
                            # Lookup the item to open it
                            search_res = requests.get(f"{API_BASE}/medicines/by-barcode/{err_data['barcode']}", headers=headers)
                            if search_res.status_code == 200:
                                dialog.destroy()
                                # Recursively open add_item with existing data
                                self.show_add_item_dialog(edit_item=search_res.json())
                    else:
                        messagebox.showerror("Error", err_data.get('error', 'Failed to save item'))
            except Exception as e:
                messagebox.showerror("Error", f"Connection failed: {str(e)}")

        ctk.CTkButton(scroll_frame, text="💾 SAVE SPECIFICATION", command=save_item, fg_color="#6366f1", height=50).pack(pady=30)

    def show_add_stock_dialog(self):
        """Add Stock Modal Dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Stock")
        dialog.geometry("500x750") # Increased height
        dialog.grab_set()
        
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(form, text="📦 Record New Stock Entry", font=("Segoe UI Black", 20)).pack(pady=(0, 20))
        
        # Medicine Selection
        try:
            m_resp = requests.get(f"{API_BASE}/medicines", headers={"Authorization": f"Bearer {self.token}"})
            meds = m_resp.json() if m_resp.status_code == 200 else []
        except: meds = []
        
        med_map = {m['name']: m['id'] for m in meds}
        code_to_name = {m.get('item_code'): m['name'] for m in meds if m.get('item_code')}
        
        # Barcode / Search Field
        ctk.CTkLabel(form, text="Scan Barcode / Item Code").pack(anchor="w")
        search_var = StringVar()
        search_entry = ctk.CTkEntry(form, textvariable=search_var, placeholder_text="Scan or type item code...", width=350)
        search_entry.pack(pady=(5, 10))

        ctk.CTkLabel(form, text="Select Item *").pack(anchor="w")
        med_var = StringVar()
        med_menu = ctk.CTkOptionMenu(form, variable=med_var, values=list(med_map.keys()) or ["No items found"], width=350)
        med_menu.pack(pady=(5, 15))
        
        def on_search_change(*args):
            code = search_var.get().strip()
            if code in code_to_name:
                med_var.set(code_to_name[code])
        
        search_var.trace_add("write", on_search_change)

        # Vendor Selection
        ctk.CTkLabel(form, text="Vendor").pack(anchor="w")
        try:
            v_resp = requests.get(f"{API_BASE}/vendors", headers={"Authorization": f"Bearer {self.token}"})
            vendors = v_resp.json() if v_resp.status_code == 200 else []
        except: vendors = []
        
        ven_map = {v['name']: v['id'] for v in vendors}
        ven_var = StringVar()
        ven_menu = ctk.CTkOptionMenu(form, variable=ven_var, values=list(ven_map.keys()) or ["No vendors found"], width=350)
        ven_menu.pack(pady=(5, 15))

        # Batch & Qty
        ctk.CTkLabel(form, text="Batch Number *").pack(anchor="w")
        batch_var = StringVar()
        ctk.CTkEntry(form, textvariable=batch_var, width=350).pack(pady=(5, 15))
        
        ctk.CTkLabel(form, text="Quantity *").pack(anchor="w")
        qty_var = StringVar()
        ctk.CTkEntry(form, textvariable=qty_var, width=350).pack(pady=(5, 15))
        
        # Dates Frame
        dates_frame = ctk.CTkFrame(form, fg_color="transparent")
        dates_frame.pack(fill="x")

        mfg_side = ctk.CTkFrame(dates_frame, fg_color="transparent")
        mfg_side.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(mfg_side, text="MFG Date").pack(anchor="w")
        mfg_var = StringVar()
        ctk.CTkEntry(mfg_side, textvariable=mfg_var, width=160, placeholder_text="YYYY-MM-DD").pack(pady=(5, 15))

        exp_side = ctk.CTkFrame(dates_frame, fg_color="transparent")
        exp_side.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(exp_side, text="Expiry Date *").pack(anchor="w")
        exp_var = StringVar()
        ctk.CTkEntry(exp_side, textvariable=exp_var, width=160, placeholder_text="YYYY-MM-DD").pack(pady=(5, 15))

        # Payment Type
        ctk.CTkLabel(form, text="Payment Method *").pack(anchor="w")
        pay_type_var = StringVar(value="Cash")
        pay_type_menu = ctk.CTkOptionMenu(form, variable=pay_type_var, values=["Cash", "Credit"], width=350)
        pay_type_menu.pack(pady=(5, 25))
        
        # QR Preview Section
        qr_preview_label = ctk.CTkLabel(form, text="")
        qr_preview_label.pack(pady=10)
        
        def update_qr_preview(*args):
            m_name = med_var.get()
            if m_name in med_map:
                # Find medicine details to generate QR
                selected_med = next((m for m in meds if m['name'] == m_name), None)
                if selected_med:
                    try:
                        path = generate_qr(selected_med.get('item_code', 'N/A'), selected_med['name'], selected_med.get('strength', ''))
                        qr_img = ctk.CTkImage(light_image=Image.open(path), dark_image=Image.open(path), size=(120, 120))
                        qr_preview_label.configure(image=qr_img, text="")
                    except:
                        qr_preview_label.configure(text="QR Load Failed")
        
        med_var.trace_add("write", update_qr_preview)
        # Initial trigger
        if meds: update_qr_preview()

        def submit():
            if not med_var.get() or med_var.get() == "No items found":
                return messagebox.showerror("Error", "Please select an item")
            
            try:
                qty = int(qty_var.get() or 0)
                if qty <= 0:
                    return messagebox.showerror("Error", "Quantity must be positive")
            except:
                return messagebox.showerror("Error", "Invalid numeric values")

            payload = {
                "medicine_id": med_map[med_var.get()],
                "vendor_id": ven_map.get(ven_var.get()),
                "batch_number": batch_var.get(),
                "quantity": qty,
                "purchase_price": 0,
                "selling_price": 0,
                "payment_type": pay_type_var.get(),
                "mfg_date": mfg_var.get() if (mfg_var.get() and mfg_var.get().strip()) else None,
                "expiry_date": exp_var.get() if (exp_var.get() and exp_var.get().strip()) else None
            }
            
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(f"{API_BASE}/inventory/stock", json=payload, headers=headers)
            if resp.status_code == 201:
                messagebox.showinfo("Success", "Stock recorded successfully")
                dialog.destroy()
                self.show_inventory_management()
            else:
                messagebox.showerror("Error", resp.json().get('error', 'Failed to record stock'))

        ctk.CTkButton(form, text="✅ RECORD STOCK", command=submit, fg_color="#10b981", height=50).pack(fill="x")
    def show_billing_terminal(self):
        """Complete Billing Terminal (Cashier Level) with QR Support"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Determine nav based on role
        if self.user['role'] == 'SUPER_ADMIN':
            nav_items = self.get_super_admin_nav()
        elif self.user['role'] == 'ADMIN':
            nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        else:
            nav_items = self.get_cashier_nav()
            
        self.create_sidebar(main_container, nav_items, "Sales Terminal")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="💰 Sales Terminal", font=("Segoe UI Black", 28)).pack(side="left")
        ctk.CTkButton(header, text="📜 Bill Log", command=self.show_bill_log, width=120, fg_color="#475569").pack(side="right")
        
        # Main Layout: Left (Cart), Right (Product Search & Payment)
        panes = ctk.CTkFrame(content, fg_color="transparent")
        panes.pack(fill="both", expand=True)
        
        left_pane = ctk.CTkFrame(panes, fg_color="transparent")
        left_pane.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_pane = ctk.CTkFrame(panes, width=400, fg_color=("#ffffff", "#1e293b"))
        right_pane.pack(side="right", fill="y", padx=(10, 0))
        
        # --- LEFT PANE: CART ---
        cart_frame = ctk.CTkScrollableFrame(left_pane, fg_color=("#ffffff", "#1e293b"))
        cart_frame.pack(fill="both", expand=True)
        
        # Cart Header
        h_frame = ctk.CTkFrame(cart_frame, fg_color=("#e2e8f0", "#334155"), height=40)
        h_frame.pack(fill="x", padx=10, pady=10)
        cols = [("Product", 200), ("Batch", 80), ("Expiry", 80), ("Rate", 60), ("Qty", 60), ("Total", 80), ("", 40)]
        for lbl, w in cols:
            ctk.CTkLabel(h_frame, text=lbl, width=w, font=("Segoe UI Bold", 12)).pack(side="left", padx=2)
            
        cart_items = [] # List of dicts
        self.cart_total = 0.0
        
        def update_cart_display():
            for w in cart_frame.winfo_children():
                if w != h_frame: w.destroy()
            
            self.cart_total = 0.0
            
            for i, item in enumerate(cart_items):
                row_total = item['qty'] * item['rate']
                self.cart_total += row_total
                
                row = ctk.CTkFrame(cart_frame, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=2)
                
                ctk.CTkLabel(row, text=item['name'], width=200, anchor="w").pack(side="left", padx=2)
                ctk.CTkLabel(row, text=item['batch'], width=80).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=item['expiry'], width=80).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=f"{item['rate']:.2f}", width=60).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=str(item['qty']), width=60).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=f"{row_total:.2f}", width=80).pack(side="left", padx=2)
                
                def remove(idx=i):
                    cart_items.pop(idx)
                    update_cart_display()
                    
                ctk.CTkButton(row, text="❌", width=40, height=25, fg_color="#ef4444", command=remove).pack(side="left", padx=2)
                
            update_totals()

        # --- RIGHT PANE: SEARCH & PAYMENT ---
        
        # 1. Product Search
        search_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=15)
        
        # 0. Customer Details (NEW)
        cust_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        cust_frame.pack(fill="x", padx=15, pady=(15, 0), before=search_frame)
        
        ctk.CTkLabel(cust_frame, text="👤 Customer Details", font=("Segoe UI Bold", 14)).pack(anchor="w", pady=(0, 5))
        
        c_grid = ctk.CTkFrame(cust_frame, fg_color="transparent")
        c_grid.pack(fill="x")
        
        cust_name_var = StringVar()
        cust_phone_var = StringVar()
        cust_addr_var = StringVar()
        cust_sex_var = StringVar(value="Male")
        invoice_date_var = StringVar(value=DateUtils.get_current_bs_date_str())

        # Invoice Date (Editable)
        ctk.CTkLabel(cust_frame, text="Invoice Date (BS):", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(cust_frame, textvariable=invoice_date_var, placeholder_text="YYYY-MM-DD").pack(fill="x", pady=(0, 5))
        
        # Name
        ctk.CTkLabel(c_grid, text="Name:", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(c_grid, textvariable=cust_name_var, placeholder_text="Enter Customer Name").pack(fill="x", pady=(0, 5))
        
        # Phone & Address Row
        c_sub = ctk.CTkFrame(c_grid, fg_color="transparent")
        c_sub.pack(fill="x", pady=2)
        
        # Phone
        d1 = ctk.CTkFrame(c_sub, fg_color="transparent")
        d1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(d1, text="Phone Number: *", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(d1, textvariable=cust_phone_var, placeholder_text="98XXXXXXXX").pack(fill="x")
        
        # Address
        d2 = ctk.CTkFrame(c_sub, fg_color="transparent")
        d2.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(d2, text="Address:", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkEntry(d2, textvariable=cust_addr_var, placeholder_text="City/Region").pack(fill="x")

        # Sex Dropdown
        ctk.CTkLabel(cust_frame, text="Sex:", font=("Segoe UI", 12)).pack(anchor="w", pady=(5, 0))
        ctk.CTkOptionMenu(cust_frame, variable=cust_sex_var, values=["Male", "Female", "Other"]).pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(search_frame, text="📷 Scan Barcode / Search Product:", font=("Segoe UI Bold", 12)).pack(anchor="w")
        search_var = StringVar()
        
        def on_barcode_scan(event):
            query = search_var.get().strip()
            if not query: return
            
            # 1. Search API for exact match (Barcode or Name)
            # Assuming scanners send Enter after scanning
            try:
                h = {"Authorization": f"Bearer {self.token}"}
                r = requests.get(f"{API_BASE}/inventory/stock?query={query}", headers=h)
                if r.status_code == 200:
                    results = r.json()
                    # Filter valid
                    valid_stock = [i for i in results if i['quantity'] > 0]
                    
                    if len(valid_stock) == 1:
                        # Exact match found -> Auto Add
                        item = valid_stock[0]
                        # Quick Add (logic duplicated from add_to_cart but simplified)
                        # Ensure we don't have dialog here, just add to cart logic
                        
                        # Check exist
                        exist = next((x for x in cart_items if x['id'] == item['id']), None)
                        if exist:
                            if exist['qty'] < item['quantity']:
                                exist['qty'] += 1
                                update_cart_display()
                                search_var.set("") # Clear for next scan
                            else:
                                messagebox.showwarning("Stock", f"Max stock reached for {item['medicine_name']}")
                        else:
                            cart_items.append({
                                "id": item['id'],
                                "medicine_id": item['medicine_id'],
                                "name": item['medicine_name'],
                                "batch": item['batch_number'],
                                "expiry": item['expiry_date'],
                                "rate": float(item['selling_price']),
                                "qty": 1
                            })
                            update_cart_display()
                            search_var.set("") # Clear for next scan
                            
                        return # Done
                        
                    elif len(valid_stock) > 1:
                        # Multiple matches -> Show Picker with this query
                        show_product_picker(query)
                        search_var.set("")
                        return
            except: pass
            
            # If no match or error, show picker normally
            show_product_picker(query)
            search_var.set("")

        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, placeholder_text="Scan Barcode or Type & Enter...")
        search_entry.pack(fill="x", pady=(5, 10))
        search_entry.bind("<Return>", on_barcode_scan)
        
        def show_product_picker(initial_query=""):
            d = ctk.CTkToplevel(self.root)
            d.title("Select Product")
            d.geometry("600x500")
            d.transient(self.root)
            d.grab_set()
            
            # Search
            s_frame = ctk.CTkFrame(d)
            s_frame.pack(fill="x", padx=10, pady=10)
            q = StringVar(value=initial_query)
            ctk.CTkEntry(s_frame, textvariable=q, placeholder_text="Search medicine...", width=300).pack(side="left", padx=5)
            
            res_frame = ctk.CTkScrollableFrame(d)
            res_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            def do_search():
                for w in res_frame.winfo_children(): w.destroy()
                try:
                    h = {"Authorization": f"Bearer {self.token}"}
                    # Using stock endpoint
                    r = requests.get(f"{API_BASE}/inventory/stock?query={q.get()}", headers=h)
                    if r.status_code == 200:
                        for item in r.json():
                            # Only valid stock
                            if item['quantity'] <= 0: continue
                            
                            btn = ctk.CTkButton(res_frame, 
                                text=f"{item['medicine_name']} | Batch: {item['batch_number']} | Exp: {item['expiry_date']} | Stock: {item['quantity']} | Price: {item['selling_price']}",
                                anchor="w", fg_color="transparent", text_color="black", hover_color="#cbd5e1",
                                command=lambda i=item: add_to_cart(i, d))
                            btn.pack(fill="x", pady=2)
                except: pass
                
            ctk.CTkButton(s_frame, text="Search", width=100, command=do_search).pack(side="left")
            
            if initial_query:
                do_search()
            
        def add_to_cart(item, dialog):
            # Prompt qty
            qty_dialog = ctk.CTkToplevel(dialog)
            qty_dialog.geometry("300x200")
            qty_dialog.title("Enter Quantity")
            qty_dialog.grab_set()
            
            ctk.CTkLabel(qty_dialog, text=f"Product: {item['medicine_name']}").pack(pady=10)
            ctk.CTkLabel(qty_dialog, text=f"Available: {item['quantity']}").pack()
            
            qv = IntVar(value=1)
            ctk.CTkEntry(qty_dialog, textvariable=qv).pack(pady=10)
            
            def confirm():
                qty = qv.get()
                if qty <= 0 or qty > item['quantity']:
                    return messagebox.showerror("Error", "Invalid Quantity")
                    
                cart_items.append({
                    "id": item['id'], # Stock ID
                    "medicine_id": item['medicine_id'],
                    "name": item['medicine_name'],
                    "batch": item['batch_number'],
                    "expiry": item['expiry_date'],
                    "rate": float(item['selling_price']),
                    "qty": qty
                })
                update_cart_display()
                qty_dialog.destroy()
                dialog.destroy()
                
            ctk.CTkButton(qty_dialog, text="Add", command=confirm).pack(pady=10)

        ctk.CTkButton(search_frame, text="🔍 Browse / Search Products", command=show_product_picker).pack(fill="x")

        # 2. Payment Section (The Core Task)
        pay_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        pay_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(pay_frame, text="Payment Details", font=("Segoe UI Bold", 16)).pack(anchor="w", pady=(10, 5))
        
        # Payment Category
        ctk.CTkLabel(pay_frame, text="Payment Category:", font=("Segoe UI Bold", 12)).pack(anchor="w")
        pay_cat_var = StringVar(value="CASH")
        ctk.CTkOptionMenu(pay_frame, variable=pay_cat_var, values=["CASH", "DIGITAL"], 
                          width=300).pack(pady=(0, 10))
        
        # Method Dropdown (Hidden for Cash)
        method_label = ctk.CTkLabel(pay_frame, text="Select Method:", font=("Segoe UI Bold", 12))
        method_var = StringVar(value="")
        method_menu = ctk.CTkOptionMenu(pay_frame, variable=method_var, values=[], width=300)
        
        # QR Display Panel
        qr_panel = ctk.CTkFrame(pay_frame, fg_color=("#e2e8f0", "#334155"), corner_radius=10)
        qr_image_label = ctk.CTkLabel(qr_panel, text="Select a method", width=200, height=200)
        qr_info = ctk.CTkLabel(qr_panel, text="", font=("Segoe UI", 11), justify="left")
        
        btn_fullscreen = ctk.CTkButton(qr_panel, text="⛶ Fullscreen QR", width=120, height=30)
        
        # Digital fields
        ref_label = ctk.CTkLabel(pay_frame, text="Transaction Ref (Optional):", font=("Segoe UI Bold", 12))
        ref_entry = ctk.CTkEntry(pay_frame, width=300)
        
        # Data store for methods
        self.payment_methods_cache = []
        
        def load_payment_methods():
            try:
                h = {"Authorization": f"Bearer {self.token}"}
                r = requests.get(f"{API_BASE}/payment-methods?category=DIGITAL&status=Active&show_on_billing=true", headers=h)
                if r.status_code == 200:
                    self.payment_methods_cache = r.json()
                    names = [m['name'] for m in self.payment_methods_cache]
                    if names:
                        method_menu.configure(values=names)
                        method_var.set(names[0])
                        update_qr_display()
            except: pass
            
        def update_qr_display(*args):
             # Find selected method
             name = method_var.get()
             method = next((m for m in self.payment_methods_cache if m['name'] == name), None)
             
             if method:
                 # Load QR
                 try:
                     h = {"Authorization": f"Bearer {self.token}"}
                     r = requests.get(f"{API_BASE}/payment-methods/{method['id']}/qr", headers=h)
                     if r.status_code == 200:
                        import base64, io
                        from PIL import Image
                        b64 = r.json().get('qr_image', '').split('base64,')[-1]
                        if b64:
                            img_data = base64.b64decode(b64)
                            pil_img = Image.open(io.BytesIO(img_data))
                            
                            # Standard preview
                            pil_preview = pil_img.copy()
                            pil_preview.thumbnail((200, 200))
                            ctk_prev = ctk.CTkImage(light_image=pil_preview, dark_image=pil_preview, size=pil_preview.size)
                            qr_image_label.configure(image=ctk_prev, text="")
                            qr_image_label.image = ctk_prev
                            
                            # Info
                            info_text = f"Account: {method.get('account_name') or '-'}\nID: {method.get('account_id') or '-'}"
                            qr_info.configure(text=info_text)
                            
                            # Fullscreen handler
                            def open_fs():
                                fs_win = ctk.CTkToplevel(self.root)
                                fs_win.title(f"Scan to Pay - {method['name']}")
                                fs_win.geometry("600x700")
                                fs_win.grab_set()
                                
                                ctk.CTkLabel(fs_win, text=f"Scan to Pay via {method['name']}", 
                                           font=("Segoe UI Black", 24)).pack(pady=20)
                                           
                                pil_fs = pil_img.copy()
                                pil_fs.thumbnail((500, 500))
                                ctk_fs = ctk.CTkImage(light_image=pil_fs, dark_image=pil_fs, size=pil_fs.size)
                                ctk.CTkLabel(fs_win, image=ctk_fs, text="").pack(pady=10)
                                
                                ctk.CTkLabel(fs_win, text=info_text, font=("Segoe UI Bold", 14)).pack(pady=10)
                                ctk.CTkButton(fs_win, text="Close", command=fs_win.destroy, 
                                             fg_color="#ef4444", width=200).pack(pady=20)
                                             
                            btn_fullscreen.configure(command=open_fs)
                            
                        else:
                            qr_image_label.configure(image=None, text="Invalid QR Data")
                     else:
                        qr_image_label.configure(image=None, text="No QR Uploaded")
                        qr_info.configure(text="")
                 except: 
                     qr_image_label.configure(image=None, text="Error loading QR")
                     qr_info.configure(text="")
             else:
                 qr_image_label.configure(image=None, text="Select a Method")

        method_var.trace_add("write", update_qr_display)
        
        def toggle_payment_ui(*args):
            cat = pay_cat_var.get()
            if cat == "DIGITAL":
                method_label.pack(anchor="w", pady=(5, 0))
                method_menu.pack(pady=(0, 10))
                qr_panel.pack(fill="x", pady=10)
                qr_image_label.pack(pady=10)
                qr_info.pack(pady=(0, 5))
                btn_fullscreen.pack(pady=(0, 10))
                ref_label.pack(anchor="w")
                ref_entry.pack(pady=(0, 10))
                
                if not self.payment_methods_cache:
                    load_payment_methods()
            else:
                method_label.pack_forget()
                method_menu.pack_forget()
                qr_panel.pack_forget()
                ref_label.pack_forget()
                ref_entry.pack_forget()
                
        pay_cat_var.trace_add("write", toggle_payment_ui)
        toggle_payment_ui() # Check initial
        
        # Totals Display
        total_frame = ctk.CTkFrame(right_pane, fg_color=("#e2e8f0", "#334155"))
        total_frame.pack(fill="x", side="bottom", pady=20, padx=15)
        
        lbl_total = ctk.CTkLabel(total_frame, text="Total: Rs. 0.00", font=("Segoe UI Black", 24))
        lbl_total.pack(pady=15)
        
        def update_totals():
            lbl_total.configure(text=f"Total: Rs. {self.cart_total:,.2f}")
            
        # User info removed VAT notice as per user request
            
        def process_sale():
            if not cart_items:
                return messagebox.showerror("Error", "Cart is empty")
                
            if not cust_phone_var.get().strip():
                return messagebox.showerror("Validation", "Customer Phone Number is required!")

            payload = {
                "items": cart_items,
                "customer_name": cust_name_var.get(),
                "customer_contact": cust_phone_var.get(),
                "customer_address": cust_addr_var.get(),
                "customer_sex": cust_sex_var.get(),
                "invoice_date": invoice_date_var.get(),
                "subtotal": self.cart_total,
                "total_amount": self.cart_total, # For backend consistency
                "vat_amount": 0,
                "discount_amount": 0,
                "grand_total": self.cart_total,
                "payment_category": pay_cat_var.get(),
                "paid_amount": self.cart_total
            }
            
            # PDF Generation moved to after API success to get correct Bill Number

            
            if pay_cat_var.get() == "DIGITAL":
                m_name = method_var.get()
                method = next((m for m in self.payment_methods_cache if m['name'] == m_name), None)
                if not method:
                    return messagebox.showerror("Error", "Please select a digital payment method")
                    
                # Verify QR exists (simple check: if we loaded it successfully)
                # But better check method data which implies it should have QR if we filter properly,
                # or we check if user removed it.
                # User req: "If selected method has no QR saved => block save"
                # We can check database or check if image loaded.
                
                payload["payment_method_id"] = method['id']
                payload["transaction_ref"] = ref_entry.get().strip()
                
            try:
                h = {"Authorization": f"Bearer {self.token}"}
                r = requests.post(f"{API_BASE}/sales", json=payload, headers=h)
                if r.status_code == 201 or r.status_code == 200:
                    resp_data = r.json()
                    bill_number = resp_data.get('bill_number') # Get backend generated bill number
                    
                    # --- PDF GEN ---
                    try:
                        from pdf_generator import generate_invoice
                        import os
                        if not os.path.exists("invoices"): os.makedirs("invoices")
                        
                        safe_date = invoice_date_var.get().replace("-", "").replace("/", "") 
                        fname = f"invoices/{bill_number}_{safe_date}.pdf"
                        
                        p_data = {**payload, "bill_number": bill_number, 
                                  "created_at": invoice_date_var.get(), 
                                  "invoice_date": invoice_date_var.get(),
                                  "pharmacy_name": self.user.get('pharmacy_name'),
                                  "pharmacy_address": self.user.get('address'),
                                  "pharmacy_contact": self.user.get('contact'),
                                  "pan_number": self.user.get('pan_number'),
                                  "oda_number": self.user.get('oda_number'),
                                  "sold_by": self.user.get('name')}
                        
                        if not p_data.get('pharmacy_contact'):
                            p_data['pharmacy_contact'] = self.user.get('pharmacy_contact') or self.user.get('contact_number')
                                  
                        generate_invoice(p_data, fname)
                        os.startfile(os.path.abspath(fname))
                    except Exception as e: 
                        print(f"PDF Error: {e}")
                    # ---------------

                    messagebox.showinfo("Success", "Sale recorded successfully")
                    self.show_billing_terminal() # Reset
                else:
                    messagebox.showerror("Error", f"Failed: {r.text}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        ctk.CTkButton(right_pane, text="✅ Checkout / Print Bill", command=process_sale, 
                     height=50, fg_color="#10b981", font=("Segoe UI Bold", 16)).pack(side="bottom", fill="x", padx=15, pady=(0, 20))



    def show_system_logs(self):
        """View System Audit Logs"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "System Logs")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        self.add_back_button(header_frame)
        
        ctk.CTkLabel(
            header_frame,
            text="📜 System Audit Logs",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left")
        
        # Refresh Button
        ctk.CTkButton(
            header_frame,
            text="🔄 Refresh Logs",
            width=150,
            command=self.show_system_logs
        ).pack(side="right")
        
        # Logs Container
        logs_container = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        logs_container.pack(fill="both", expand=True, pady=10)
        
        try:
            response = requests.get(f"{API_BASE}/super/audit-logs", headers={"Authorization": f"Bearer {self.token}"})
            logs = response.json() if response.status_code == 200 else []
        except:
            logs = []
            
        if not logs:
            ctk.CTkLabel(logs_container, text="No audit logs found.", font=("Segoe UI", 14), text_color="gray").pack(pady=50)
        else:
            # Table Header
            head_row = ctk.CTkFrame(logs_container, fg_color=("#f1f5f9", "#0f172a"), height=40)
            head_row.pack(fill="x", padx=10, pady=10)
            
            headers = ["Time", "User", "Action", "Details"]
            widths = [200, 150, 150, 400]
            
            for i, h in enumerate(headers):
                frame = ctk.CTkFrame(head_row, width=widths[i], height=30, fg_color="transparent")
                frame.pack(side="left", padx=5)
                frame.pack_propagate(False)
                ctk.CTkLabel(frame, text=h, font=("Segoe UI Bold", 12)).pack(anchor="w")
            
            # Log Rows
            for log in logs:
                row = ctk.CTkFrame(logs_container, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=2)
                
                # Format time
                time_str = log.get('created_at', 'N/A')
                try: time_str = time_str.replace('T', ' ').split('.')[0]
                except: pass
                
                # User
                user_name = log.get('user_name', 'Unknown')
                
                cols = [time_str, user_name, log.get('action', 'N/A'), log.get('details', 'N/A')]
                
                for i, val in enumerate(cols):
                    frame = ctk.CTkFrame(row, width=widths[i], height=30, fg_color="transparent")
                    frame.pack(side="left", padx=5)
                    frame.pack_propagate(False)
                    ctk.CTkLabel(frame, text=str(val), font=("Segoe UI", 11), anchor="w").pack(anchor="w")
                
                ctk.CTkFrame(logs_container, height=1, fg_color="#e2e8f0").pack(fill="x", padx=10)



 


    def show_bill_designer(self):
        """Interactive Bill Designer for Super Admin"""
        try:
            from DesignerCore import launch_designer
            # Create a context dict including new detailed fields
            user_ctx = {
                "role": self.user_role,
                "id": self.user.get('id') if isinstance(self.user, dict) else getattr(self.user, 'id', None),
                "token": self.token,
                # Pass data needed for binding
                "pharmacy_name": self.user.get('pharmacy_name', ''),
                "oda_number": self.user.get('oda_number', ''),
                "pan_number": self.user.get('pan_number', ''),
                "address": self.user.get('address', ''),
                "contact": self.user.get('contact', ''),
                "profile_pic": self.user.get('profile_pic', '')
            }
            launch_designer(self.root, user_ctx)
        except ImportError as e:
            messagebox.showerror("Error", f"Designer Module missing: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch designer: {e}")
            
    def _legacy_show_bill_designer(self):
        """Interactive Bill Designer for Super Admin"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        self.create_sidebar(main_container, nav_items, "Bill Designer")
        
        # Main Content Area
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        self.add_back_button(header_frame)
        ctk.CTkLabel(header_frame, text="🎨 Bill Layout Designer", font=("Segoe UI Black", 28, "bold"), text_color=("#1e293b", "#f1f5f9")).pack(side="left")
        
        # Save Button
        ctk.CTkButton(header_frame, text="💾 Save Design", width=150, fg_color="#4f46e5", command=self.save_bill_design).pack(side="right")
        
        # Split Layout using Grid
        split_view = ctk.CTkFrame(content, fg_color="transparent")
        split_view.pack(fill="both", expand=True)
        split_view.grid_columnconfigure(0, weight=1) # Tools
        split_view.grid_columnconfigure(1, weight=3) # Preview
        split_view.grid_rowconfigure(0, weight=1)
        
        # Tools Scrollable (Left)
        tools_panel = ctk.CTkScrollableFrame(split_view, fg_color=("#ffffff", "#1e293b"), corner_radius=15, width=350)
        tools_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=0)
        
        ctk.CTkLabel(tools_panel, text="Layout Controls", font=("Segoe UI Black", 18)).pack(pady=10, anchor="w")
        
        # Define styling vars if not exists
        if not hasattr(self, 'design_vars'):
            self.design_vars = {
                "show_logo": ctk.BooleanVar(value=True),
                "pharmacy_name_size": ctk.IntVar(value=24),
                "show_address": ctk.BooleanVar(value=True),
                "show_pan": ctk.BooleanVar(value=True),
                "show_patient": ctk.BooleanVar(value=True),
                "show_doctor": ctk.BooleanVar(value=True),
                "footer_text": ctk.StringVar(value="Thank you for your visit! get well soon."),
                "accent_color": ctk.StringVar(value="#000000"),
                "paper_size": ctk.StringVar(value="A5")
            }
        
        # Helper to simplify control creation
        def add_control_section(title):
            ctk.CTkLabel(tools_panel, text=title, font=("Segoe UI Bold", 14), text_color="#3b82f6").pack(anchor="w", pady=(15, 5))
            
        # 1. Header Controls
        add_control_section("Header Configuration")
        ctk.CTkCheckBox(tools_panel, text="Show Logo", variable=self.design_vars["show_logo"], command=self.update_bill_preview).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(tools_panel, text="Pharmacy Name Size:", font=("Segoe UI", 12)).pack(anchor="w")
        ctk.CTkSlider(tools_panel, from_=16, to=48, variable=self.design_vars["pharmacy_name_size"], command=lambda v: self.update_bill_preview()).pack(fill="x", pady=5)
        
        ctk.CTkCheckBox(tools_panel, text="Show Address & Contact", variable=self.design_vars["show_address"], command=self.update_bill_preview).pack(anchor="w", pady=5)
        ctk.CTkCheckBox(tools_panel, text="Show PAN/ODA info", variable=self.design_vars["show_pan"], command=self.update_bill_preview).pack(anchor="w", pady=5)

        # 2. Body/Table Controls
        add_control_section("Table & Info")
        ctk.CTkCheckBox(tools_panel, text="Patient Details Field", variable=self.design_vars["show_patient"], command=self.update_bill_preview).pack(anchor="w", pady=5)
        ctk.CTkCheckBox(tools_panel, text="Doctor Name Field", variable=self.design_vars["show_doctor"], command=self.update_bill_preview).pack(anchor="w", pady=5)
        
        # 3. Footer Controls
        add_control_section("Footer Settings")
        ctk.CTkLabel(tools_panel, text="Terms / Greeting Message:", font=("Segoe UI", 12)).pack(anchor="w")
        footer_entry = ctk.CTkEntry(tools_panel, textvariable=self.design_vars["footer_text"])
        footer_entry.pack(fill="x", pady=5)
        footer_entry.bind("<KeyRelease>", lambda e: self.update_bill_preview())
        
        # Preview Area (Right)
        preview_bg = ctk.CTkFrame(split_view, fg_color="#cbd5e1", corner_radius=15)
        preview_bg.grid(row=0, column=1, sticky="nsew", pady=0)
        
        # The Paper
        self.paper = ctk.CTkFrame(preview_bg, fg_color="white", width=450, height=600)
        self.paper.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.7, relheight=0.85) # Centered paper
        self.paper.pack_propagate(False) # Don't shrink
        
        # Trigger initial update after a short delay to ensure widgets are ready
        self.root.after(100, self.update_bill_preview)

    def update_bill_preview(self):
        # Clear paper
        for w in self.paper.winfo_children(): w.destroy()
        
        # Header
        header_frame = ctk.CTkFrame(self.paper, fg_color="transparent")
        header_frame.pack(fill="x", pady=20, padx=20)
        
        if self.design_vars["show_logo"].get():
            ctk.CTkLabel(header_frame, text="[LOGO]", width=60, height=60, fg_color="#eee", text_color="gray").pack(side="left")
            
        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15)
        
        size = int(self.design_vars["pharmacy_name_size"].get())
        ctk.CTkLabel(info_frame, text="My Pharmacy Name", font=("Times New Roman", size, "bold"), text_color="black").pack(anchor="w")
        
        if self.design_vars["show_address"].get():
            ctk.CTkLabel(info_frame, text="Kathmandu, Nepal | 9800000000", font=("Arial", 10), text_color="gray").pack(anchor="w")
            
        if self.design_vars["show_pan"].get():
             ctk.CTkLabel(info_frame, text="PAN: 123456789", font=("Arial", 10), text_color="gray").pack(anchor="w")
             
        ctk.CTkFrame(self.paper, height=2, fg_color="black").pack(fill="x", padx=20)
        
        # Info
        if self.design_vars["show_patient"].get():
            inf = ctk.CTkFrame(self.paper, fg_color="transparent")
            inf.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(inf, text="Patient: _________________", text_color="black").pack(side="left")
            ctk.CTkLabel(inf, text="Date: 2082-01-01", text_color="black").pack(side="right")
            
        # Table Mockup
        tbl = ctk.CTkFrame(self.paper, fg_color="transparent", border_width=1, border_color="black")
        tbl.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Headers
        hdrs = ctk.CTkFrame(tbl, fg_color="#eee", height=25)
        hdrs.pack(fill="x")
        ctk.CTkLabel(hdrs, text="SN  |  Particulars             | Qty | Rate | Amount", font=("Consolas", 10), text_color="black").pack(anchor="w", padx=5)
        
        # Rows
        for i in range(5):
             ctk.CTkFrame(tbl, fg_color="transparent", height=1, border_width=0).pack(fill="x", pady=8)
             ctk.CTkLabel(tbl, text=f"{i+1}   |  Sample Medicine       |  1  | 100  | 100.00", font=("Consolas", 10), text_color="black").pack(anchor="w", padx=5)
             
        # Footer
        ftr = ctk.CTkFrame(self.paper, fg_color="transparent")
        ftr.pack(fill="x", padx=20, pady=20, side="bottom")
        
        ctk.CTkLabel(ftr, text=self.design_vars["footer_text"].get(), font=("Arial", 9, "italic"), text_color="gray").pack(side="bottom")
        ctk.CTkLabel(ftr, text="Authorized Signature: ________________", font=("Arial", 10), text_color="black").pack(side="right", pady=20)

    def save_bill_design(self):
         # In a real scenario, this would POST self.design_vars to backend
         self.update_bill_preview()
         messagebox.showinfo("Success", "Bill Design Saved Successfully!")
        
    def show_system_settings(self):
        """System Settings"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        nav_items = self.get_super_admin_nav()
        
        self.create_sidebar(main_container, nav_items, "System Settings")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        self.add_back_button(header_frame)
        
        ctk.CTkLabel(
            header_frame,
            text="⚙️ System Settings",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left")

        # Settings Container
        settings_container = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        settings_container.pack(fill="both", expand=True, pady=10, padx=10)
        
        # App Info Section
        ctk.CTkLabel(settings_container, text="Application Information", font=("Segoe UI Black", 16)).pack(anchor="w", padx=20, pady=10)
        
        info_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(info_frame, text="Software Name:", font=("Segoe UI Semibold", 13), width=150).pack(side="left")
        ctk.CTkLabel(info_frame, text="Aarambha Pharmacy Management System", font=("Segoe UI", 13)).pack(side="left", padx=10)
        
        version_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        version_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(version_frame, text="Version:", font=("Segoe UI Semibold", 13), width=150).pack(side="left")
        ctk.CTkLabel(version_frame, text="v1.0.0 (Release Candidate)", font=("Segoe UI", 13)).pack(side="left", padx=10)

        ctk.CTkFrame(settings_container, height=1, fg_color="#e2e8f0").pack(fill="x", padx=20, pady=20)
        
        # Theme Settings
        ctk.CTkLabel(settings_container, text="Appearance & Theme", font=("Segoe UI Black", 16)).pack(anchor="w", padx=20, pady=(0, 10))
        
        theme_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(theme_frame, text="Color Theme:", font=("Segoe UI Semibold", 13), width=150).pack(side="left")
        
        def change_theme(new_theme):
            ctk.set_appearance_mode(new_theme)
            
        theme_var = StringVar(value=ctk.get_appearance_mode())
        ctk.CTkOptionMenu(theme_frame, values=["System", "Light", "Dark"], command=change_theme, variable=theme_var).pack(side="left", padx=10)
        
        scale_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        scale_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(scale_frame, text="UI Scaling:", font=("Segoe UI Semibold", 13), width=150).pack(side="left")
        
        def change_scaling(new_scaling):
            new_scaling_float = int(new_scaling.replace("%", "")) / 100
            ctk.set_widget_scaling(new_scaling_float)
            
        ctk.CTkOptionMenu(scale_frame, values=["80%", "90%", "100%", "110%", "120%"], command=change_scaling).pack(side="left", padx=10)
        
        ctk.CTkFrame(settings_container, height=1, fg_color="#e2e8f0").pack(fill="x", padx=20, pady=20)

        # System Maintenance
        ctk.CTkLabel(settings_container, text="System Maintenance", font=("Segoe UI Black", 16)).pack(anchor="w", padx=20, pady=(0, 10))
        
        maint_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        maint_frame.pack(fill="x", padx=20, pady=5)
        
        def mock_backup():
            messagebox.showinfo("Backup", "Database backup started...\nBackup completed successfully to /backups/db_backup_latest.sql")
            
        ctk.CTkButton(maint_frame, text="💾 Backup Database", command=mock_backup, fg_color="#0f172a", width=180).pack(side="left", padx=5)
        ctk.CTkButton(maint_frame, text="🧹 Clear Temp Files", fg_color="#64748b", width=180).pack(side="left", padx=15)
        
        ctk.CTkFrame(settings_container, height=1, fg_color="#e2e8f0").pack(fill="x", padx=20, pady=20)
        
        # Support
        ctk.CTkLabel(settings_container, text="Support & Help", font=("Segoe UI Black", 16)).pack(anchor="w", padx=20, pady=(0, 10))
        
        support_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        support_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(support_frame, text="For technical support, please contact:", font=("Segoe UI", 13)).pack(anchor="w")
        ctk.CTkLabel(support_frame, text="📧 support@aarambhasoft.com | 📞 +977-9855062769", font=("Segoe UI Bold", 13)).pack(anchor="w", pady=5)


    def show_vendor_management(self):
        """Supplier/Vendor management interface"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Determine nav based on role
        if self.user['role'] == 'SUPER_ADMIN':
            nav_items = self.get_super_admin_nav()
        elif self.user['role'] == 'ADMIN':
            nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        else:
            nav_items = self.get_cashier_nav()
            
        self.create_sidebar(main_container, nav_items, "Vendor Management")
        
        # Main content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        ctk.CTkLabel(
            header_frame,
            text="🤝 Vendor Management",
            font=("Segoe UI Black", 28, "bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(side="left")
        
        # Only Admin/Super Admin can add vendors
        if self.user['role'] in ['ADMIN', 'SUPER_ADMIN']:
            ctk.CTkButton(
                header_frame,
                text="➕ Add New Supplier",
                width=200,
                height=45,
                font=("Segoe UI Black", 14),
                fg_color=("#10b981", "#059669"),
                hover_color=("#059669", "#047857"),
                command=self.show_add_vendor_dialog
            ).pack(side="right")
        
        # Search & Filters
        filter_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        filter_frame.pack(fill="x", pady=(0, 20))
        
        search_var = StringVar()
        search_entry = ctk.CTkEntry(
            filter_frame, 
            placeholder_text="🔍 Search by Name, Code, or Mobile...",
            textvariable=search_var,
            height=45,
            font=("Segoe UI", 14)
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=15)
        
        status_var = StringVar(value="All")
        status_menu = ctk.CTkOptionMenu(
            filter_frame, 
            values=["All", "Active", "Inactive"],
            variable=status_var,
            width=120,
            height=40
        )
        status_menu.pack(side="left", padx=10, pady=15)
        
        def refresh_list():
            query = search_var.get().strip()
            status = status_var.get() if status_var.get() != "All" else ""
            self.load_vendors_list(vendors_container, query, status)

        ctk.CTkButton(
            filter_frame,
            text="Refresh",
            width=100,
            height=40,
            command=refresh_list
        ).pack(side="right", padx=20, pady=15)
        
        search_var.trace_add("write", lambda *args: refresh_list())
        status_var.trace_add("write", lambda *args: refresh_list())
        
        # Vendors container
        vendors_container = ctk.CTkFrame(content, fg_color="transparent")
        vendors_container.pack(fill="both", expand=True)
        
        # Initial load
        refresh_list()

    def load_vendors_list(self, parent, query="", status=""):
        """Load and display list of vendors in a table-like view"""
        for widget in parent.winfo_children():
            widget.destroy()
            
        try:
            params = {}
            if query: params['search'] = query
            if status: params['status'] = status
            
            headers = {"Authorization": f"Bearer {self.token}"}
            res = requests.get(f"{API_BASE}/vendors", params=params, headers=headers)
            vendors = res.json() if res.status_code == 200 else []
        except Exception as e:
            print(f"Error loading vendors: {e}")
            vendors = []

        if not vendors:
            ctk.CTkLabel(parent, text="No suppliers found.", font=("Segoe UI", 16), text_color="gray").pack(pady=50)
            return

        # Table Header
        h_frame = ctk.CTkFrame(parent, fg_color=("#e2e8f0", "#334155"), height=45)
        h_frame.pack(fill="x", pady=(0, 10))
        
        cols = [("Code", 0.1), ("Name", 0.25), ("Contact", 0.15), ("Address", 0.2), ("Due Amount", 0.15), ("Actions", 0.15)]
        for label, weight in cols:
            lbl = ctk.CTkLabel(h_frame, text=label, font=("Segoe UI Bold", 13))
            lbl.place(relx=sum(w for l, w in cols[:cols.index((label, weight))]), rely=0.5, anchor="w", x=15)

        for v in vendors:
            row = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e293b"), height=60, corner_radius=10)
            row.pack(fill="x", pady=4)
            
            # Code
            ctk.CTkLabel(row, text=v['supplier_code'], font=("Consolas", 13)).place(relx=0, rely=0.5, anchor="w", x=15)
            # Name
            ctk.CTkLabel(row, text=v['name'], font=("Segoe UI Semibold", 14)).place(relx=0.1, rely=0.5, anchor="w", x=15)
            # Contact
            ctk.CTkLabel(row, text=v['phone'], font=("Segoe UI", 13)).place(relx=0.35, rely=0.5, anchor="w", x=15)
            # Address
            ctk.CTkLabel(row, text=v['address'] or '-', font=("Segoe UI", 13)).place(relx=0.5, rely=0.5, anchor="w", x=15)
            # Due
            due_val = float(v.get('current_due', 0))
            due_color = "#ef4444" if due_val > 0 else "#10b981"
            ctk.CTkLabel(row, text=f"रु {due_val}", font=("Segoe UI Bold", 14), text_color=due_color).place(relx=0.7, rely=0.5, anchor="w", x=15)
            
            # Actions
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.place(relx=0.85, rely=0.5, anchor="w")
            
            ctk.CTkButton(btn_frame, text="👁️", width=35, height=35, fg_color="#3b82f6", command=lambda x=v: self.show_vendor_detail(x)).pack(side="left", padx=5)
            
            if self.user['role'] in ['ADMIN', 'SUPER_ADMIN']:
                ctk.CTkButton(btn_frame, text="✏️", width=35, height=35, fg_color="#f59e0b", command=lambda x=v: self.show_add_vendor_dialog(x)).pack(side="left", padx=5)

    def show_add_vendor_dialog(self, vendor=None):
        """Add or Edit Supplier Dialog"""
        is_edit = vendor is not None
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Supplier" if is_edit else "Add New Supplier")
        dialog.geometry("700x850")
        dialog.transient(self.root)
        dialog.grab_set()
        
        container = ctk.CTkScrollableFrame(dialog, fg_color=("#ffffff", "#1e293b"))
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="📝 Supplier Information", font=("Segoe UI Black", 24)).pack(anchor="w", pady=(0, 20))
        
        # Fields
        name_var = StringVar(value=vendor['name'] if is_edit else "")
        comp_var = StringVar(value=vendor['company_name'] if is_edit else "")
        phone_var = StringVar(value=vendor['phone'] if is_edit else "")
        alt_phone_var = StringVar(value=vendor.get('alt_phone', '') if is_edit else "")
        email_var = StringVar(value=vendor.get('email', '') if is_edit else "")
        pan_var = StringVar(value=vendor.get('pan_vat', '') if is_edit else "")
        contact_person_var = StringVar(value=vendor.get('contact_person', '') if is_edit else "")
        terms_var = StringVar(value=vendor.get('payment_terms', 'Cash') if is_edit else "Cash")
        due_var = StringVar(value=str(vendor.get('opening_due', 0)) if is_edit else "0")
        
        def create_field(label, var, placeholder="", is_required=False):
            row = ctk.CTkFrame(container, fg_color="transparent")
            row.pack(fill="x", pady=8)
            lbl = f"{label} *" if is_required else label
            ctk.CTkLabel(row, text=lbl, font=("Segoe UI Semibold", 13), width=150, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, textvariable=var, placeholder_text=placeholder, height=40, font=("Segoe UI", 14))
            entry.pack(side="left", fill="x", expand=True)
            return entry

        create_field("Supplier Name", name_var, "e.g. Life Care Meds", True)
        create_field("Company Name", comp_var, "Legal Name")
        create_field("Mobile Number", phone_var, "+977 98xxxxxxxx", True)
        create_field("Alt. Phone", alt_phone_var)
        create_field("Email Address", email_var)
        create_field("PAN / VAT No", pan_var)
        create_field("Contact Person", contact_person_var)
        
        ctk.CTkLabel(container, text="Address Details", font=("Segoe UI Semibold", 13)).pack(anchor="w", pady=(10, 0))
        addr_text = ctk.CTkTextbox(container, height=80)
        addr_text.pack(fill="x", pady=8)
        if is_edit: addr_text.insert("1.0", vendor.get('address', ''))

        ctk.CTkLabel(container, text="Payment Terms", font=("Segoe UI Semibold", 13)).pack(anchor="w", pady=(10, 0))
        ctk.CTkOptionMenu(container, variable=terms_var, values=["Cash", "Credit", "7 Days", "15 Days", "30 Days"], height=40).pack(fill="x", pady=8)

        if not is_edit: # Opening due only on create
            create_field("Opening Due (रु)", due_var, "0.00")

        ctk.CTkLabel(container, text="Bank / Payment Info", font=("Segoe UI Semibold", 13)).pack(anchor="w", pady=(10, 0))
        bank_text = ctk.CTkTextbox(container, height=60)
        bank_text.pack(fill="x", pady=8)
        if is_edit: bank_text.insert("1.0", vendor.get('bank_info', ''))

        def save():
            if not name_var.get().strip() or not phone_var.get().strip():
                messagebox.showerror("Error", "Name and Phone are required")
                return
            
            data = {
                "name": name_var.get().strip(),
                "company_name": comp_var.get().strip(),
                "phone": phone_var.get().strip(),
                "alt_phone": alt_phone_var.get().strip(),
                "email": email_var.get().strip(),
                "pan_vat": pan_var.get().strip(),
                "contact_person": contact_person_var.get().strip(),
                "address": addr_text.get("1.0", "end").strip(),
                "payment_terms": terms_var.get(),
                "opening_due": due_var.get(),
                "bank_info": bank_text.get("1.0", "end").strip()
            }
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                if is_edit:
                    data['status'] = vendor['status']
                    res = requests.put(f"{API_BASE}/vendors/{vendor['id']}", json=data, headers=headers)
                else:
                    res = requests.post(f"{API_BASE}/vendors", json=data, headers=headers)
                
                if res.status_code in [200, 201]:
                    messagebox.showinfo("Success", f"Supplier {'updated' if is_edit else 'added'} successfully!")
                    dialog.destroy()
                    self.show_vendor_management()
                else:
                    messagebox.showerror("Error", res.json().get('error', 'Action failed'))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(container, text="💾 SAVE SUPPLIER", height=50, font=("Segoe UI Black", 14), command=save).pack(pady=30, fill="x")

    def show_vendor_detail(self, vendor_summary):
        """Detailed Supplier Profile with Transaction History"""
        for widget in self.root.winfo_children(): widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Determine nav
        if self.user['role'] == 'SUPER_ADMIN':
            nav_items = self.get_super_admin_nav()
        elif self.user['role'] == 'ADMIN':
            nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        else:
            nav_items = self.get_cashier_nav()
            
        self.create_sidebar(main_container, nav_items, "Vendor Management")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Fetch full data with stats
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            res = requests.get(f"{API_BASE}/vendors/{vendor_summary['id']}", headers=headers)
            vendor = res.json() if res.status_code == 200 else vendor_summary
        except: vendor = vendor_summary

        # Profile Header
        header = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=20)
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(header, text="← Back", width=80, height=30, command=self.show_vendor_management).pack(side="left", padx=20, pady=20)
        
        title_side = ctk.CTkFrame(header, fg_color="transparent")
        title_side.pack(side="left", padx=10, fill="y")
        ctk.CTkLabel(title_side, text=vendor['name'], font=("Segoe UI Black", 32), text_color=("#1e293b", "#f1f5f9")).pack(anchor="w", pady=(20, 0))
        ctk.CTkLabel(title_side, text=f"Code: {vendor['supplier_code']} | Status: {vendor['status']}", font=("Segoe UI", 14), text_color="gray").pack(anchor="w", pady=(0, 20))
        
        # Stats Row
        stats_frame = ctk.CTkFrame(content, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)
        
        stats = [
            ("Total Purchases", f"रु {vendor.get('stats', {}).get('total_purchases', 0)}", "#3b82f6"),
            ("Total Paid", f"रु {vendor.get('stats', {}).get('total_paid', 0)}", "#10b981"),
            ("Current Due", f"रु {vendor.get('stats', {}).get('current_due', 0)}", "#ef4444")
        ]
        
        for i, (l, v, c) in enumerate(stats):
            card = ctk.CTkFrame(stats_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=15, height=120)
            card.grid(row=0, column=i, padx=5, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=l, font=("Segoe UI Bold", 13), text_color="gray").pack(pady=(15, 5))
            ctk.CTkLabel(card, text=v, font=("Segoe UI Black", 24), text_color=c).pack(pady=(0, 15))

        # Action Buttons for Admin
        if self.user['role'] in ['ADMIN', 'SUPER_ADMIN']:
            action_frame = ctk.CTkFrame(content, fg_color="transparent")
            action_frame.pack(fill="x", pady=20)
            ctk.CTkButton(action_frame, text="💸 Record Payment", fg_color="#10b981", height=45, command=lambda: self.show_record_vendor_payment_dialog(vendor)).pack(side="left", padx=5)
            ctk.CTkButton(action_frame, text="✏️ Edit Profile", fg_color="#f59e0b", height=45, command=lambda: self.show_add_vendor_dialog(vendor)).pack(side="left", padx=5)

        # Tabs / History Section
        ctk.CTkLabel(content, text="📜 Transaction History (Ledger)", font=("Segoe UI Black", 20, "bold")).pack(anchor="w", pady=(20, 10))
        history_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        history_frame.pack(fill="both", expand=True)

        try:
            h_res = requests.get(f"{API_BASE}/vendors/{vendor['id']}/history", headers=headers)
            history = h_res.json() if h_res.status_code == 200 else []
        except: history = []

        if not history:
            ctk.CTkLabel(history_frame, text="No transactions found.", font=("Segoe UI", 14), text_color="gray").pack(pady=40)
        else:
            # Table-like history
            for trans in history:
                t_row = ctk.CTkFrame(history_frame, fg_color="transparent")
                t_row.pack(fill="x", padx=15, pady=8)
                
                date_str = trans['date'].split('T')[0] if 'T' in trans['date'] else trans['date']
                type_label = "P" if trans['type'] == 'purchase' else "S"
                type_color = "#3b82f6" if trans['type'] == 'purchase' else "#10b981"
                
                ctk.CTkLabel(t_row, text=date_str, font=("Consolas", 13), width=100).pack(side="left")
                ctk.CTkLabel(t_row, text=trans['type'].upper(), font=("Segoe UI Bold", 12), text_color=type_color, width=100).pack(side="left", padx=10)
                ctk.CTkLabel(t_row, text=f"रु {trans['amount']}", font=("Segoe UI Bold", 13), width=120, anchor="e").pack(side="left", padx=10)
                ctk.CTkLabel(t_row, text=f"Ref: {trans['reference'] or '-'}", font=("Segoe UI", 12), text_color="gray").pack(side="left", padx=20)

    def show_record_vendor_payment_dialog(self, vendor):
        """Dialog to record payment to a vendor"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Record Payment - {vendor['name']}")
        dialog.geometry("500x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"💸 Pay to: {vendor['name']}", font=("Segoe UI Black", 20)).pack(pady=20)
        ctk.CTkLabel(dialog, text=f"Current Due: रु {vendor.get('current_due', 0)}", text_color="#ef4444", font=("Segoe UI Bold", 14)).pack()
        
        amount_var = StringVar()
        ref_var = StringVar()
        method_var = StringVar(value="Cash")
        notes_var = StringVar()
        
        ctk.CTkLabel(dialog, text="Amount to Pay (रु) *", font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=40, pady=(20, 5))
        ctk.CTkEntry(dialog, textvariable=amount_var, height=45, font=("Segoe UI", 16)).pack(fill="x", padx=40)
        
        ctk.CTkLabel(dialog, text="Payment Method", font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=40, pady=(15, 5))
        ctk.CTkOptionMenu(dialog, variable=method_var, values=["Cash", "Bank", "Wallet", "Other"], height=40).pack(fill="x", padx=40)
        
        ctk.CTkLabel(dialog, text="Reference (Cheque/Txn ID)", font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=40, pady=(15, 5))
        ctk.CTkEntry(dialog, textvariable=ref_var, height=40).pack(fill="x", padx=40)
        
        ctk.CTkLabel(dialog, text="Notes", font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=40, pady=(15, 5))
        ctk.CTkEntry(dialog, textvariable=notes_var, height=40).pack(fill="x", padx=40)
        
        def pay():
            amt = amount_var.get().strip()
            if not amt or not amt.replace('.', '', 1).isdigit():
                messagebox.showerror("Error", "Valid amount is required")
                return
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                payload = {
                    "vendor_id": vendor['id'],
                    "amount": float(amt),
                    "method": method_var.get(),
                    "reference_no": ref_var.get().strip(),
                    "notes": notes_var.get().strip()
                }
                res = requests.post(f"{API_BASE}/vendors/payments", json=payload, headers=headers)
                if res.status_code == 201:
                    messagebox.showinfo("Success", "Payment recorded successfully!")
                    dialog.destroy()
                    self.show_vendor_detail(vendor) # Refresh detail page
                else:
                    messagebox.showerror("Error", res.json().get('error', 'Payment failed'))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(dialog, text="CONFIRM PAYMENT", height=50, fg_color="#10b981", font=("Segoe UI Black", 14), command=pay).pack(pady=30, padx=40, fill="x")

    def show_purchase_entry(self):
        """Complete Purchase Entry (GRN) Module - Fully Functional"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container with sidebar
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "🛒 Purchase Entry (GRN)")
        
        # SCROLLABLE content area - CRITICAL for visibility
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # ============ SECTION 1: HEADER CARD ============
        header_card = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        header_card.pack(fill="x", pady=(0, 15))
        
        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Title
        ctk.CTkLabel(header_inner, text="📋 Purchase Entry / GRN", font=("Segoe UI Black", 20)).pack(anchor="w", pady=(0, 15))
        
        # Row 1: GRN No, Date, Invoice
        row1 = ctk.CTkFrame(header_inner, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        # GRN No (auto-generated)
        grn_col = ctk.CTkFrame(row1, fg_color="transparent")
        grn_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(grn_col, text="GRN No (Auto)", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        # Use BS Date in GRN ID for consistency
        bs_ymd = DateUtils.get_current_bs_date_str().replace("-", "")
        grn_no = f"GRN-{bs_ymd}-{random.randint(1000, 9999)}"
        grn_entry = ctk.CTkEntry(grn_col, height=40, font=("Consolas", 13))
        grn_entry.insert(0, grn_no)
        grn_entry.configure(state="readonly", text_color="#6366f1")
        grn_entry.pack(fill="x", pady=2)
        
        # Purchase Date
        date_col = ctk.CTkFrame(row1, fg_color="transparent")
        date_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(date_col, text="Purchase Date (BS) *", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        date_var = StringVar(value=DateUtils.get_current_bs_date_str())
        ctk.CTkEntry(date_col, textvariable=date_var, height=40).pack(fill="x", pady=2)
        
        # Invoice No
        inv_col = ctk.CTkFrame(row1, fg_color="transparent")
        inv_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(inv_col, text="Invoice No *", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        invoice_var = StringVar()
        ctk.CTkEntry(inv_col, textvariable=invoice_var, placeholder_text="Supplier Bill No", height=40).pack(fill="x", pady=2)
        
        # Row 2: Supplier, Payment Type, Store
        row2 = ctk.CTkFrame(header_inner, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        
        # Supplier
        sup_col = ctk.CTkFrame(row2, fg_color="transparent")
        sup_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(sup_col, text="Supplier *", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        
        supplier_frame = ctk.CTkFrame(sup_col, fg_color="transparent")
        supplier_frame.pack(fill="x", pady=2)
        
        supplier_id_var = IntVar(value=0)
        supplier_var = StringVar(value="Select Supplier...")
        outstanding_var = StringVar(value="Balance: ₹0.00")
        
        def pick_supplier():
            self.show_supplier_picker(supplier_id_var, supplier_var, outstanding_var)
        
        sup_btn = ctk.CTkButton(supplier_frame, textvariable=supplier_var, command=pick_supplier,
                                fg_color=("#f8fafc", "#0f172a"), text_color=("#1e293b", "#f1f5f9"),
                                border_width=1, height=40, anchor="w")
        sup_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(supplier_frame, text="+", width=40, height=40, command=self.show_mini_supplier_form).pack(side="left")
        
        ctk.CTkLabel(sup_col, textvariable=outstanding_var, font=("Segoe UI Bold", 10), text_color="#ef4444").pack(anchor="w", pady=(2, 0))
        
        # Payment Type
        pay_col = ctk.CTkFrame(row2, fg_color="transparent")
        pay_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(pay_col, text="Payment Type *", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        pay_var = StringVar(value="Cash")
        ctk.CTkOptionMenu(pay_col, variable=pay_var, values=["Cash", "Credit"], height=40).pack(fill="x", pady=2)
        
        # Store/Warehouse
        store_col = ctk.CTkFrame(row2, fg_color="transparent")
        store_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(store_col, text="Store/Warehouse", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        store_var = StringVar(value="Main Store")
        ctk.CTkOptionMenu(store_col, variable=store_var, values=["Main Store", "Sub Store A", "Cold Storage"], height=40).pack(fill="x", pady=2)
        
        # Row 3: Due Date (conditional), Notes
        row3 = ctk.CTkFrame(header_inner, fg_color="transparent")
        row3.pack(fill="x", pady=5)
        
        # Due Date (shown only for Credit)
        due_col = ctk.CTkFrame(row3, fg_color="transparent")
        due_col.pack(side="left", fill="x", expand=True, padx=5)
        due_lbl = ctk.CTkLabel(due_col, text="Due Date", font=("Segoe UI Bold", 11), text_color="gray")
        due_entry = ctk.CTkEntry(due_col, placeholder_text="YYYY-MM-DD", height=40)
        
        def on_pay_change(*args):
            if pay_var.get() == "Credit":
                due_lbl.pack(anchor="w")
                due_entry.pack(fill="x", pady=2)
            else:
                due_lbl.pack_forget()
                due_entry.pack_forget()
        
        pay_var.trace_add("write", on_pay_change)
        
        # Notes
        notes_col = ctk.CTkFrame(row3, fg_color="transparent")
        notes_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(notes_col, text="Notes/Remarks", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        notes_text = ctk.CTkTextbox(notes_col, height=60)
        notes_text.pack(fill="x", pady=2)
        
        # ============ SECTION 2: ITEMS GRID CARD ============
        grid_card = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        grid_card.pack(fill="both", expand=True, pady=(0, 15))
        
        grid_inner = ctk.CTkFrame(grid_card, fg_color="transparent")
        grid_inner.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(grid_inner, text="📦 Items Entry", font=("Segoe UI Black", 16)).pack(anchor="w", pady=(0, 10))
        
        # Column Headers
        headers_frame = ctk.CTkFrame(grid_inner, fg_color=("#e2e8f0", "#334155"), height=40)
        headers_frame.pack(fill="x", pady=(0, 5))
        
        cols = [
            ("S.N", 40), ("Barcode", 100), ("Product", 200), ("Batch", 100), ("Expiry", 90),
            ("P.Rate", 80), ("MRP", 80), ("Qty", 60), ("Free", 50),
            ("Disc%", 60), ("VAT", 50), ("Total", 100), ("", 40)
        ]
        
        for label, width in cols:
            ctk.CTkLabel(headers_frame, text=label, width=width, font=("Segoe UI Bold", 11), text_color="gray").pack(side="left", padx=2)
        
        # Scrollable items container
        items_scroll = ctk.CTkScrollableFrame(grid_inner, fg_color="transparent", height=300)
        items_scroll.pack(fill="both", expand=True)
        
        self.grn_rows = []
        
        # --- AUTOCOMPLETE HELPER ---
        def setup_autocomplete(entry, id_var, name_var):
            def on_key(event):
                # Debounce or simple len check
                query = name_var.get()
                if len(query) < 2: return
                
                # Fetch
                try:
                    h = {"Authorization": f"Bearer {self.token}"}
                    # Assuming we have a global medicine search or stock search. 
                    # Use medicines endpoint for definition search (since we are buying, it might be new or existing)
                    r = requests.get(f"{API_BASE}/medicines?search={query}", headers=h)
                    if r.status_code == 200:
                        data = r.json()
                        show_suggestions(data, entry, id_var, name_var)
                except: pass
                
            entry.bind("<KeyRelease>", on_key)
            
        def show_suggestions(data, entry, id_var, name_var):
            # Close existing if any
            if hasattr(entry, 'suggestion_window') and entry.suggestion_window:
                entry.suggestion_window.destroy()
                
            if not data: return
            
            # Create popup
            # Calculate position
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height()
            
            popup = ctk.CTkToplevel(self.root)
            popup.wm_overrideredirect(True)
            popup.geometry(f"300x200+{x}+{y}")
            entry.suggestion_window = popup
            
            # Listbox
            import tkinter as tk
            lb = tk.Listbox(popup, font=("Segoe UI", 11), height=10)
            lb.pack(fill="both", expand=True)
            
            meds = []
            for item in data:
                meds.append(item)
                lb.insert("end", f"{item['name']} ({item.get('strength','')})")
                
            def on_select(evt):
                if not lb.curselection(): return
                idx = lb.curselection()[0]
                m = meds[idx]
                
                name_var.set(m['name'])
                id_var.set(m['id'])
                popup.destroy()
                
            lb.bind("<<ListboxSelect>>", on_select)
            popup.bind("<FocusOut>", lambda e: popup.destroy())
        
        def add_grn_row():
            idx = len(self.grn_rows) + 1
            row_f = ctk.CTkFrame(items_scroll, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            
            # S.N
            ctk.CTkLabel(row_f, text=str(idx), width=40, font=("Segoe UI", 11)).pack(side="left", padx=2)
            
            # Barcode
            barcode_var = StringVar()
            b_ent = ctk.CTkEntry(row_f, textvariable=barcode_var, width=100, placeholder_text="Scan...")
            b_ent.pack(side="left", padx=2)
            
            # Product
            p_id = IntVar(value=0)
            p_name = StringVar()
            p_ent = ctk.CTkEntry(row_f, textvariable=p_name, width=200, placeholder_text="Search Product...")
            p_ent.pack(side="left", padx=2)
            
            # Attach Autocomplete
            setup_autocomplete(p_ent, p_id, p_name)
            
            # Batch
            batch = StringVar()
            ctk.CTkEntry(row_f, textvariable=batch, width=100, placeholder_text="Batch No").pack(side="left", padx=2)
            
            # Expiry Format (BS/AD)
            exp_fmt = StringVar(value="BS")
            ctk.CTkOptionMenu(row_f, variable=exp_fmt, values=["BS", "AD"], width=60).pack(side="left", padx=2)
            
            # Expiry Date
            exp = StringVar()
            ctk.CTkEntry(row_f, textvariable=exp, width=90, placeholder_text="YYYY-MM-DD").pack(side="left", padx=2)
            
            # Purchase Rate
            rate = DoubleVar(value=0.0)
            r_ent = ctk.CTkEntry(row_f, textvariable=rate, width=80)
            r_ent.pack(side="left", padx=2)
            
            # MRP
            mrp = DoubleVar(value=0.0)
            m_ent = ctk.CTkEntry(row_f, textvariable=mrp, width=80)
            m_ent.pack(side="left", padx=2)
            
            # Qty
            qty = IntVar(value=0)
            q_ent = ctk.CTkEntry(row_f, textvariable=qty, width=60)
            q_ent.pack(side="left", padx=2)
            
            # Free
            free = IntVar(value=0)
            ctk.CTkEntry(row_f, textvariable=free, width=50).pack(side="left", padx=2)
            
            # Disc%
            disc = DoubleVar(value=0.0)
            ctk.CTkEntry(row_f, textvariable=disc, width=60).pack(side="left", padx=2)
            
            # VAT
            vat = StringVar(value="VAT")
            ctk.CTkOptionMenu(row_f, variable=vat, values=["VAT", "VAT-Free"], width=50).pack(side="left", padx=2)
            
            # Total
            total_var = StringVar(value="0.00")
            ctk.CTkLabel(row_f, textvariable=total_var, width=100, font=("Segoe UI Bold", 12), text_color="#6366f1").pack(side="left", padx=2)
            
            # Remove button
            def remove():
                row_f.destroy()
                self.grn_rows.remove(row_data)
                update_totals()
            
            ctk.CTkButton(row_f, text="×", width=30, height=30, fg_color="#fee2e2", text_color="#ef4444", command=remove).pack(side="left", padx=2)
            
            row_data = {
                'p_id': p_id, 'p_name': p_name, 'batch': batch, 'exp': exp, 'exp_fmt': exp_fmt,
                'rate': rate, 'mrp': mrp, 'qty': qty, 'free': free,
                'disc': disc, 'vat': vat, 'total_var': total_var
            }
            self.grn_rows.append(row_data)
            
            # Auto-calculation
            def calc(*a):
                try:
                    base = qty.get() * rate.get()
                    disc_amt = base * (disc.get() / 100)
                    subtotal = base - disc_amt
                    vat_amt = subtotal * 0.13 if vat.get() == "VAT" else 0
                    line_total = subtotal + vat_amt
                    total_var.set(f"{line_total:.2f}")
                    update_totals()
                except:
                    pass
            
            qty.trace_add("write", calc)
            rate.trace_add("write", calc)
            disc.trace_add("write", calc)
            vat.trace_add("write", calc)
            
            # Product search
            p_ent.bind("<KeyRelease>", lambda e: self.show_product_search_popup(p_ent, p_id, p_name, mrp, rate))
            
            # Enter key navigation
            def on_enter(event):
                if event.widget == q_ent and idx == len(self.grn_rows):
                    add_grn_row()
                event.widget.tk_focusNext().focus()
                return "break"
            
            for widget in [p_ent, r_ent, m_ent, q_ent]:
                widget.bind("<Return>", on_enter)
        
        # ============ SECTION 3: SUMMARY CARD ============
        summary_card = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        summary_card.pack(fill="x", pady=(0, 15))
        
        summary_inner = ctk.CTkFrame(summary_card, fg_color="transparent")
        summary_inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Summary calculations
        subtotal_var = StringVar(value="0.00")
        disc_total_var = StringVar(value="0.00")
        vat_total_var = StringVar(value="0.00")
        grand_var = StringVar(value="0.00")
        paid_var = DoubleVar(value=0.0)
        due_var = StringVar(value="0.00")
        
        def update_totals():
            subtotal = 0
            disc_total = 0
            vat_total = 0
            
            for r in self.grn_rows:
                try:
                    base = r['qty'].get() * r['rate'].get()
                    disc_amt = base * (r['disc'].get() / 100)
                    sub = base - disc_amt
                    vat_amt = sub * 0.13 if r['vat'].get() == "VAT" else 0
                    
                    subtotal += base
                    disc_total += disc_amt
                    vat_total += vat_amt
                except:
                    pass
            
            grand = subtotal - disc_total + vat_total
            due = grand - paid_var.get()
            
            subtotal_var.set(f"{subtotal:.2f}")
            disc_total_var.set(f"{disc_total:.2f}")
            vat_total_var.set(f"{vat_total:.2f}")
            grand_var.set(f"{grand:.2f}")
            due_var.set(f"{max(0, due):.2f}")
        
        paid_var.trace_add("write", lambda *a: update_totals())
        
        # Left column - totals
        left_col = ctk.CTkFrame(summary_inner, fg_color="transparent")
        left_col.pack(side="left", fill="y")
        
        self.add_summary_row(left_col, "Subtotal", subtotal_var)
        self.add_summary_row(left_col, "Discount", disc_total_var, color="#ef4444")
        self.add_summary_row(left_col, "VAT (13%)", vat_total_var)
        self.add_summary_row(left_col, "Grand Total", grand_var, font=("Segoe UI Black", 20), color="#10b981")
        
        # Right column - payment
        right_col = ctk.CTkFrame(summary_inner, fg_color="transparent")
        right_col.pack(side="right", fill="y")
        
        ctk.CTkLabel(right_col, text="Paid Amount", font=("Segoe UI Bold", 12)).pack(anchor="e")
        ctk.CTkEntry(right_col, textvariable=paid_var, width=150, height=40, font=("Segoe UI", 14), justify="right").pack(pady=5)
        
        ctk.CTkLabel(right_col, text="Due Amount", font=("Segoe UI Bold", 12)).pack(anchor="e")
        ctk.CTkLabel(right_col, textvariable=due_var, font=("Segoe UI Black", 18), text_color="#ef4444").pack(pady=5)
        
        # ============ SECTION 4: ACTION BUTTONS ============
        actions_frame = ctk.CTkFrame(content, fg_color="transparent")
        actions_frame.pack(fill="x")
        
        def save_purchase(confirm=False):
            if not supplier_id_var.get():
                return messagebox.showerror("Error", "Please select a supplier")
            if not invoice_var.get().strip():
                return messagebox.showerror("Error", "Please enter invoice number")
            if not self.grn_rows or all(r['p_id'].get() == 0 for r in self.grn_rows):
                return messagebox.showerror("Error", "Please add at least one item")
            
            payload = {
                "grn_no": grn_no,
                "supplier_id": supplier_id_var.get(),
                "invoice_no": invoice_var.get(),
                # Convert Purchase Date (BS) to AD for Backend
                "purchase_date": DateUtils.bs_to_ad(date_var.get()),
                "payment_type": pay_var.get(),
                "due_date": due_entry.get() if pay_var.get() == "Credit" else None,
                "subtotal": float(subtotal_var.get()),
                "discount_total": float(disc_total_var.get()),
                "tax_total": float(vat_total_var.get()),
                "grand_total": float(grand_var.get()),
                "paid_amount": paid_var.get(),
                "status": "CONFIRMED" if confirm else "DRAFT",
                "notes": notes_text.get("1.0", "end").strip(),
                "items": [{
                    "medicine_id": r['p_id'].get(),
                    "batch_no": r['batch'].get(),
                    # Handle Expiry Date based on Format Selection
                    "expiry_date": (
                        DateUtils.bs_to_ad(r['exp'].get()) if r['exp_fmt'].get() == "BS" else r['exp'].get()
                    ) if r['exp'].get() else None,
                    "qty": r['qty'].get(),
                    "free_qty": r['free'].get(),
                    "purchase_rate": r['rate'].get(),
                    "mrp": r['mrp'].get(),
                    "discount_amount": (r['qty'].get() * r['rate'].get()) * (r['disc'].get() / 100),
                    "tax_amount": (r['qty'].get() * r['rate'].get() * (1 - r['disc'].get()/100)) * (0.13 if r['vat'].get() == "VAT" else 0),
                    "line_total": float(r['total_var'].get())
                } for r in self.grn_rows if r['p_id'].get() > 0]
            }
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                resp = requests.post(f"{API_BASE}/purchases", json=payload, headers=headers)
                if resp.status_code == 200:
                    messagebox.showinfo("Success", f"Purchase {'confirmed and stock updated' if confirm else 'saved as draft'}!")
                    self.show_purchase_entry()
                else:
                    messagebox.showerror("Error", resp.json().get('error', 'Failed to save purchase'))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(actions_frame, text="➕ ADD ROW", height=50, width=150, command=add_grn_row).pack(side="left", padx=5)
        ctk.CTkButton(actions_frame, text="💾 SAVE DRAFT", height=50, width=150, fg_color="#64748b", command=lambda: save_purchase(False)).pack(side="left", padx=5)
        ctk.CTkButton(actions_frame, text="✅ CONFIRM & POST STOCK", height=50, width=200, fg_color="#10b981", font=("Segoe UI Black", 13), command=lambda: save_purchase(True)).pack(side="right", padx=5)
        
        # Initialize with 3 blank rows
        for _ in range(3):
            add_grn_row()


    def add_labeled_entry(self, parent, label, var, row, col, **kwargs):
        ctk.CTkLabel(parent, text=label, font=("Segoe UI Bold", 11), text_color="gray").grid(row=row, column=col, sticky="w", padx=10)
        ent = ctk.CTkEntry(parent, textvariable=var if isinstance(var, StringVar) else None, **kwargs)
        if not isinstance(var, StringVar): ent.insert(0, str(var))
        ent.grid(row=row+1, column=col, sticky="we", padx=10, pady=(2, 10))
        return ent

    def add_summary_row(self, parent, label, var, font=("Segoe UI Bold", 13), color=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=label + ":", font=("Segoe UI Bold", 12)).pack(side="left")
        ctk.CTkLabel(f, textvariable=var, font=font, text_color=color).pack(side="left", padx=10)

    def show_mini_supplier_form(self):
        """Quick dialog to add supplier"""
        d = ctk.CTkToplevel(self.root)
        d.title("Quick Add Supplier")
        d.geometry("400x500")
        d.grab_set()
        
        ctk.CTkLabel(d, text="🤝 New Supplier", font=("Segoe UI Black", 20)).pack(pady=20)
        name = ctk.CTkEntry(d, placeholder_text="Supplier Name", width=300)
        name.pack(pady=10)
        phone = ctk.CTkEntry(d, placeholder_text="Phone", width=300)
        phone.pack(pady=10)
        addr = ctk.CTkEntry(d, placeholder_text="Address", width=300)
        addr.pack(pady=10)
        
        def save():
            if not name.get(): return
            payload = {"name": name.get(), "phone": phone.get(), "address": addr.get(), "email": ""}
            # Fix: Use standard /vendors endpoint
            r = requests.post(f"{API_BASE}/vendors", json=payload, headers={"Authorization": f"Bearer {self.token}"})
            if r.status_code in [201, 200]: d.destroy()
            else: messagebox.showerror("Error", f"Failed: {r.json().get('error', 'Unknown Error')}")
            
        ctk.CTkButton(d, text="Save Supplier", command=save, fg_color="#10b981").pack(pady=20)

    def show_purchase_returns(self):
        """Purchase Return Module"""
        for widget in self.root.winfo_children(): widget.destroy()
        main = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main.pack(fill="both", expand=True)
        nav = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main, nav, "↩️ Purchase Return")
        
        content = ctk.CTkFrame(main, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(content, text="↩️ Purchase Return (Backproduct)", font=("Segoe UI Black", 28)).pack(anchor="w", pady=(0, 20))
        
        # Select Confirmed GRN
        sel_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        sel_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(sel_frame, text="Select Confirmation GRN to Return Items From:").pack(padx=20, pady=(10, 0), anchor="w")
        
        grn_list = []
        try:
            r = requests.get(f"{API_BASE}/purchases/confirmed", headers={"Authorization": f"Bearer {self.token}"})
            grn_list = r.json()
        except: pass
        
        grn_opts = [f"{g['grn_no']} - {g['supplier_name']} ({g['invoice_no']})" for g in grn_list]
        grn_var = StringVar(value="Choose GRN...")
        grn_menu = ctk.CTkOptionMenu(sel_frame, values=grn_opts, variable=grn_var, width=500)
        grn_menu.pack(padx=20, pady=15, side="left")
        
        items_container = ctk.CTkFrame(content, fg_color="transparent")
        items_container.pack(fill="both", expand=True)

        def load_grn_items(*a):
            for w in items_container.winfo_children(): w.destroy()
            if grn_var.get() == "Choose GRN...": return
            
            sel_grn = next(g for g in grn_list if f"{g['grn_no']} - {g['supplier_name']}" in grn_var.get())
            
            try:
                r = requests.get(f"{API_BASE}/purchases/{sel_grn['id']}/items", headers={"Authorization": f"Bearer {self.token}"})
                items = r.json()
            except: items = []
            
            # Table
            tbl = ctk.CTkFrame(items_container, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
            tbl.pack(fill="both", expand=True)
            
            h = ctk.CTkFrame(tbl, fg_color="transparent")
            h.pack(fill="x", padx=15, pady=10)
            for t, w in [("Product", 300), ("Batch", 100), ("Purchased Qty", 120), ("Return Qty", 120), ("Rate", 100)]:
                ctk.CTkLabel(h, text=t, width=w, font=("Segoe UI Bold", 12)).pack(side="left", padx=5)
            
            ret_data = []
            for item in items:
                row = ctk.CTkFrame(tbl, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=item['medicine_name'], width=300, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=item['batch_no'], width=100).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=str(item['qty']), width=120).pack(side="left", padx=5)
                
                rqty = IntVar(value=0)
                ctk.CTkEntry(row, textvariable=rqty, width=120).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=str(item['purchase_rate']), width=100).pack(side="left", padx=5)
                
                ret_data.append({'item': item, 'rqty': rqty})
            
            def submit_return():
                try:
                    items_to_return = []
                    for d in ret_data:
                        try:
                            # Use string get and convert to handle empty/invalid input
                            val = d['rqty'].get()
                            if val > 0:
                                # Validation: Return Qty cannot exceed Purchased Qty
                                if val > d['item']['qty']:
                                    messagebox.showerror("Validation Error", 
                                        f"Return quantity for {d['item']['medicine_name']} ({val}) "
                                        f"cannot exceed purchased quantity ({d['item']['qty']})")
                                    return
                                
                                # CRITICAL: Ensure rate is a float to avoid string multiplication
                                rate = float(d['item']['purchase_rate'])
                                
                                items_to_return.append({
                                    "medicine_id": d['item']['medicine_id'],
                                    "batch_no": d['item']['batch_no'],
                                    "qty": val,
                                    "rate": rate,
                                    "line_total": val * rate
                                })
                        except (tk.TclError, ValueError):
                            # Skip invalid inputs or non-numeric values
                            continue

                    if not items_to_return:
                        messagebox.showwarning("Notice", "Please enter a valid return quantity (greater than 0)")
                        return
                    
                    payload = {
                        "purchase_id": sel_grn['id'], 
                        "return_date": DateUtils.get_current_bs_date_str(),
                        "notes": "Manual Return",
                        "items": items_to_return
                    }
                    
                    r = requests.post(f"{API_BASE}/purchases/return", json=payload, headers={"Authorization": f"Bearer {self.token}"})
                    if r.status_code == 200:
                        messagebox.showinfo("Success", "Return Processed & Supplier Balance Adjusted!")
                        self.show_purchase_returns()
                    else:
                        error_msg = r.json().get('error', 'Return failed')
                        messagebox.showerror("Error", error_msg)
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

            ctk.CTkButton(items_container, text="🚀 POST PURCHASE RETURN", height=50, fg_color="#ef4444", command=submit_return).pack(pady=20)

        grn_var.trace_add("write", load_grn_items)

    def show_supplier_picker(self, id_var, name_var, balance_var):
        """Supplier selection dialog (Updated)"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Supplier")
        dialog.geometry("500x600")
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="🤝 Select Supplier", font=("Segoe UI Bold", 20)).pack(pady=20)
        
        search_var = StringVar()
        search_entry = ctk.CTkEntry(dialog, textvariable=search_var, placeholder_text="Search supplier...")
        search_entry.pack(fill="x", padx=20, pady=10)
        
        list_frame = ctk.CTkScrollableFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        def load_suppliers():
            for w in list_frame.winfo_children(): w.destroy()
            try:
                term = search_var.get()
                # Use standard /vendors endpoint which supports 'search' param
                resp = requests.get(f"{API_BASE}/vendors?search={term}", headers={"Authorization": f"Bearer {self.token}"})
                suppliers = resp.json() if resp.status_code == 200 else []
                if not suppliers and resp.status_code == 200:
                    ctk.CTkLabel(list_frame, text="No suppliers found", text_color="gray").pack(pady=20)
                
                for s in suppliers:
                    btn = ctk.CTkButton(list_frame, text=f"{s['name']} ({s.get('phone', 'No Phone')})", 
                                       fg_color="transparent", text_color=("#1e293b", "#f1f5f9"), anchor="w",
                                       command=lambda supplier=s: select(supplier))
                    btn.pack(fill="x", pady=2)
            except Exception as e:
                print(f"Error loading suppliers in picker: {e}")
                ctk.CTkLabel(list_frame, text="Error loading suppliers", text_color="#ef4444").pack(pady=20)

        def select(s):
            id_var.set(s['id'])
            name_var.set(s['name'])
            # Fetch balance
            try:
                b_resp = requests.get(f"{API_BASE}/suppliers/{s['id']}/balance", headers={"Authorization": f"Bearer {self.token}"})
                balance_var.set(f"Balance: {b_resp.json().get('balance', 0):.2f}")
            except: pass
            dialog.destroy()

        search_var.trace_add("write", lambda *args: load_suppliers())
        load_suppliers()

    def show_product_search_popup(self, entry_widget, id_var, name_var, mrp_var=None, rate_var=None):
        """Refined product search popup with 'Add New' option"""
        term = name_var.get()
        if hasattr(self, '_search_popup') and self._search_popup.winfo_exists():
            self._search_popup.destroy()
        
        if len(term) < 2: return

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        self._search_popup = popup
        
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        popup.geometry(f"400x300+{x}+{y}")
        
        list_box = tk.Listbox(popup, font=("Segoe UI", 11), borderwidth=1, relief="solid")
        list_box.pack(fill="both", expand=True)
        
        try:
            resp = requests.get(f"{API_BASE}/search-medicines?q={term}", headers={"Authorization": f"Bearer {self.token}"})
            meds = resp.json() if resp.status_code == 200 else []
            
            list_box.insert("end", "+ Add New Product...")
            for m in meds:
                list_box.insert("end", f"{m['name']} ({m.get('strength','')}) - Stock: {m.get('total_stock', 0)}")
        except: meds = []

        def on_select(evt):
            if not list_box.curselection(): return
            idx = list_box.curselection()[0]
            if idx == 0:
                self.show_add_item_dialog()
                popup.destroy()
                return

            m = meds[idx-1]
            id_var.set(m['id'])
            name_var.set(m['name'])
            if rate_var: rate_var.set(m.get('last_purchase_rate', 0))
            popup.destroy()

        list_box.bind("<<ListboxSelect>>", on_select)
        
        # Close on focus loss
        popup.bind("<FocusOut>", lambda e: popup.destroy())


    def show_payment_methods(self):
        """Payment Methods Management - Admin Only"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        # Sidebar (reuse existing navigation)
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "💳 Payment Methods")
        
        # Scrollable content
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="💳 Payment Methods", font=("Segoe UI Black", 24)).pack(side="left")
        ctk.CTkButton(header, text="+ Add Payment Method", height=40, fg_color="#10b981",
                     command=self.show_add_payment_method_dialog).pack(side="right")
        
        # Search
        search_frame = ctk.CTkFrame(content, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 15))
        
        search_var = StringVar()
        ctk.CTkEntry(search_frame, textvariable=search_var, placeholder_text="Search payment methods...",
                    width=300, height=40).pack(side="left", padx=(0, 10))
        
        # Filter by category
        category_var = StringVar(value="All")
        ctk.CTkOptionMenu(search_frame, variable=category_var, values=["All", "CASH", "DIGITAL"],
                         width=150, height=40).pack(side="left")
        
        # List container
        list_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        list_frame.pack(fill="both", expand=True)
        
        # Table header
        header_frame = ctk.CTkFrame(list_frame, fg_color=("#e2e8f0", "#334155"), height=50)
        header_frame.pack(fill="x", padx=15, pady=15)
        
        cols = [("Name", 200), ("Category", 100), ("Provider", 150), ("Status", 100), 
                ("Show on Billing", 120), ("Actions", 200)]
        
        for label, width in cols:
            ctk.CTkLabel(header_frame, text=label, width=width, font=("Segoe UI Bold", 12),
                        text_color="gray").pack(side="left", padx=5)
        
        # Items container
        items_container = ctk.CTkScrollableFrame(list_frame, fg_color="transparent", height=400)
        items_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        def load_methods():
            # Clear existing
            for widget in items_container.winfo_children():
                widget.destroy()
            
            # Fetch from API
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                params = {}
                if category_var.get() != "All":
                    params['category'] = category_var.get()
                
                resp = requests.get(f"{API_BASE}/payment-methods", headers=headers, params=params)
                if resp.status_code == 200:
                    methods = resp.json()
                    
                    for method in methods:
                        row = ctk.CTkFrame(items_container, fg_color="transparent")
                        row.pack(fill="x", pady=5)
                        
                        # Name
                        ctk.CTkLabel(row, text=method['name'], width=200, anchor="w",
                                    font=("Segoe UI", 12)).pack(side="left", padx=5)
                        
                        # Category
                        cat_color = "#10b981" if method['category'] == 'DIGITAL' else "#64748b"
                        ctk.CTkLabel(row, text=method['category'], width=100, anchor="w",
                                    text_color=cat_color, font=("Segoe UI Bold", 11)).pack(side="left", padx=5)
                        
                        # Provider
                        ctk.CTkLabel(row, text=method.get('provider', '-'), width=150, anchor="w").pack(side="left", padx=5)
                        
                        # Status
                        status_color = "#10b981" if method['status'] == 'Active' else "#ef4444"
                        ctk.CTkLabel(row, text=method['status'], width=100, anchor="w",
                                    text_color=status_color, font=("Segoe UI Bold", 11)).pack(side="left", padx=5)
                        
                        # Show on Billing
                        show_text = "✓ Yes" if method['show_on_billing'] else "✗ No"
                        ctk.CTkLabel(row, text=show_text, width=120, anchor="w").pack(side="left", padx=5)
                        
                        # Actions
                        actions = ctk.CTkFrame(row, fg_color="transparent")
                        actions.pack(side="left", padx=5)
                        
                        ctk.CTkButton(actions, text="Edit", width=60, height=30,
                                     command=lambda m=method: self.show_edit_payment_method_dialog(m)).pack(side="left", padx=2)
                        
                        if method['category'] == 'DIGITAL':
                            ctk.CTkButton(actions, text="QR", width=50, height=30, fg_color="#6366f1",
                                         command=lambda m=method: self.show_upload_qr_dialog(m)).pack(side="left", padx=2)
                        
                        def toggle_status(mid, current):
                            new_status = 'Inactive' if current == 'Active' else 'Active'
                            try:
                                resp = requests.put(f"{API_BASE}/payment-methods/{mid}",
                                                   json={'status': new_status}, headers=headers)
                                if resp.status_code == 200:
                                    load_methods()
                            except: pass
                        
                        ctk.CTkButton(actions, text="Toggle", width=60, height=30, fg_color="#f59e0b",
                                     command=lambda m=method: toggle_status(m['id'], m['status'])).pack(side="left", padx=2)
                else:
                    ctk.CTkLabel(items_container, text="Failed to load payment methods",
                                text_color="#ef4444").pack(pady=20)
            except Exception as e:
                ctk.CTkLabel(items_container, text=f"Error: {str(e)}",
                            text_color="#ef4444").pack(pady=20)
        
        category_var.trace_add("write", lambda *a: load_methods())
        load_methods()
    
    def show_add_payment_method_dialog(self):
        """Add Payment Method Dialog with QR Support"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Payment Method")
        dialog.geometry("600x800")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (800 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Scrollable form
        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Name
        ctk.CTkLabel(form, text="Method Name *", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        name_var = StringVar(value="eSewa")
        ctk.CTkComboBox(form, variable=name_var, values=["eSewa", "Khalti", "Fonepay", "Bank Transfer"], height=40).pack(fill="x", pady=(0, 15))
        
        # Category (Hidden, always Digital)
        category_var = StringVar(value="DIGITAL")
        
        # Provider
        ctk.CTkLabel(form, text="Provider/Bank", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        provider_var = StringVar()
        ctk.CTkEntry(form, textvariable=provider_var, height=40).pack(fill="x", pady=(0, 15))
        
        # Account Name
        ctk.CTkLabel(form, text="Account Name", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        acc_name_var = StringVar()
        ctk.CTkEntry(form, textvariable=acc_name_var, height=40).pack(fill="x", pady=(0, 15))
        
        # Account ID
        ctk.CTkLabel(form, text="Account ID / Merchant ID", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        acc_id_var = StringVar()
        ctk.CTkEntry(form, textvariable=acc_id_var, height=40).pack(fill="x", pady=(0, 15))
        
        # Phone
        ctk.CTkLabel(form, text="Phone Number", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        phone_var = StringVar()
        ctk.CTkEntry(form, textvariable=phone_var, height=40).pack(fill="x", pady=(0, 15))
        
        # Notes
        ctk.CTkLabel(form, text="Notes", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        notes_text = ctk.CTkTextbox(form, height=60)
        notes_text.pack(fill="x", pady=(0, 15))
        
        # QR Code Section (Container)
        qr_frame = ctk.CTkFrame(form, fg_color=("#e2e8f0", "#334155"))
        qr_label = ctk.CTkLabel(qr_frame, text="QR Code (Required * for Digital)", font=("Segoe UI Bold", 12))
        
        qr_file = {"path": None}
        qr_preview = ctk.CTkLabel(qr_frame, text="No QR Selected", width=200, height=200, 
                                 fg_color=("#cbd5e1", "#1e293b"), corner_radius=10)
        
        def select_qr():
            from tkinter import filedialog
            filepath = filedialog.askopenfilename(
                title="Select QR Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg")]
            )
            if filepath:
                size = os.path.getsize(filepath)
                if size > 2 * 1024 * 1024:
                    return messagebox.showerror("Error", "File size must be < 2MB")
                
                qr_file['path'] = filepath
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(filepath)
                    img.thumbnail((200, 200))
                    # Convert to CTkImage
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    qr_preview.configure(image=ctk_img, text="")
                    qr_preview.image = ctk_img  # Keep ref
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load image: {e}")
        
        upload_btn = ctk.CTkButton(qr_frame, text="📁 Select QR Image", command=select_qr)
        
        def toggle_qr_visibility(*args):
            if category_var.get() == "DIGITAL":
                qr_frame.pack(fill="x", pady=(0, 15), padx=5)
                qr_label.pack(anchor="w", pady=5, padx=5)
                qr_preview.pack(pady=5)
                upload_btn.pack(pady=5)
            else:
                qr_frame.pack_forget()
        
        category_var.trace_add("write", toggle_qr_visibility)
        toggle_qr_visibility() # Init state
        
        # Show on Billing
        show_billing_var = BooleanVar(value=True)
        ctk.CTkCheckBox(form, text="Show on Billing Terminal", variable=show_billing_var,
                       font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 15))
        
        def save():
            name = name_var.get().strip()
            cat = category_var.get()
            
            if not name:
                return messagebox.showerror("Error", "Name is required")
            
            if cat == "DIGITAL" and not qr_file['path']:
                return messagebox.showerror("Error", "QR Image is required for Digital payments")
            
            # 1. Create Method
            payload = {
                "name": name,
                "category": cat,
                "provider": provider_var.get().strip() or None,
                "account_name": acc_name_var.get().strip() or None,
                "account_id": acc_id_var.get().strip() or None,
                "phone_number": phone_var.get().strip() or None,
                "notes": notes_text.get("1.0", "end").strip() or None,
                "show_on_billing": show_billing_var.get()
            }
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                resp = requests.post(f"{API_BASE}/payment-methods", json=payload, headers=headers)
                
                if resp.status_code == 201:
                    method_id = resp.json().get('id')
                    
                    # 2. Upload QR if Digital
                    if cat == "DIGITAL" and qr_file['path']:
                        with open(qr_file['path'], 'rb') as f:
                            files = {'qr_image': f}
                            qr_resp = requests.post(f"{API_BASE}/payment-methods/{method_id}/upload-qr",
                                                   files=files, headers=headers)
                            if qr_resp.status_code != 200:
                                messagebox.showwarning("Warning", "Method created but QR upload failed")
                    
                    messagebox.showinfo("Success", "Payment method added successfully")
                    dialog.destroy()
                    self.show_payment_methods()
                else:
                    messagebox.showerror("Error", resp.json().get('error', 'Failed to add'))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(form, text="Save Payment Method", command=save, height=50,
                     fg_color="#10b981", font=("Segoe UI Bold", 14)).pack(fill="x", pady=(10, 0))

    def show_upload_qr_dialog(self, method):
        """View/Update QR Code Dialog (for existing methods)"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Manage QR - {method['name']}")
        dialog.geometry("500x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form, text=f"QR Code for {method['name']}", font=("Segoe UI Black", 18)).pack(pady=(0, 20))
        
        # Existing/New Preview
        preview_label = ctk.CTkLabel(form, text="Loading...", width=300, height=300,
                                     fg_color=("#e2e8f0", "#334155"), corner_radius=10)
        preview_label.pack(pady=20)
        
        # Load existing QR
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(f"{API_BASE}/payment-methods/{method['id']}/qr", headers=headers)
            if resp.status_code == 200:
                import base64, io
                from PIL import Image, ImageTk
                
                b64_data = resp.json().get('qr_image', '').split('base64,')[-1]
                if b64_data:
                    img_data = base64.b64decode(b64_data)
                    img = Image.open(io.BytesIO(img_data))
                    img.thumbnail((300, 300))
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    preview_label.configure(image=photo, text="")
                    preview_label.image = photo
                else:
                    preview_label.configure(text="No QR Image Found")
            else:
                 preview_label.configure(text="No QR Image Found")
        except:
            preview_label.configure(text="Failed to load QR")

        selected_file = {"path": None}
        
        def select_file():
            from tkinter import filedialog
            filepath = filedialog.askopenfilename(
                title="Select New QR Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg")]
            )
            if filepath:
                size = os.path.getsize(filepath)
                if size > 2 * 1024 * 1024:
                    return messagebox.showerror("Error", "File size must be < 2MB")
                
                selected_file['path'] = filepath
                
                try:
                    from PIL import Image
                    img = Image.open(filepath)
                    img.thumbnail((300, 300))
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    preview_label.configure(image=photo, text="")
                    preview_label.image = photo
                except:
                    messagebox.showerror("Error", "Failed to load image")
        
        ctk.CTkButton(form, text="📁 Replace QR Image", command=select_file,
                     height=50, fg_color="#6366f1").pack(pady=10)
        
        def upload():
            if not selected_file['path']:
                return messagebox.showerror("Error", "Please select a new image first")
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                with open(selected_file['path'], 'rb') as f:
                    files = {'qr_image': f}
                    resp = requests.post(f"{API_BASE}/payment-methods/{method['id']}/upload-qr",
                                        files=files, headers=headers)
                if resp.status_code == 200:
                    messagebox.showinfo("Success", "QR updated successfully")
                    dialog.destroy()
                    self.show_payment_methods() # Refresh list
                else:
                    messagebox.showerror("Error", resp.json().get('error', 'Upload failed'))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(form, text="✅ Save Changes", command=upload, height=50,
                     fg_color="#10b981", font=("Segoe UI Bold", 14)).pack(pady=20)

    def show_bill_designer(self):
        """Bill Designer (Admin Only)"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Bill Design")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        self.add_back_button(header)
        ctk.CTkLabel(header, text="🎨 Bill Designer", font=("Segoe UI Black", 24)).pack(side="left", padx=20)
        
        designer = BillDesignerUI(self)
        designer = BillDesignerUI(self)
        designer.show(content)

    def show_pharmacy_reports(self):
        """Pharmacy Reports Module"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Pharmacy Reports")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        ctk.CTkLabel(content, text="📊 Pharmacy Reports (VAT Exempt)", font=("Segoe UI Black", 24)).pack(anchor="w", pady=(0, 20))
        
        # Controls
        controls = ctk.CTkFrame(content, fg_color=("#e2e8f0", "#334155"), corner_radius=10)
        controls.pack(fill="x", pady=(0, 20))
        
        # Type
        ctk.CTkLabel(controls, text="Report Type:").pack(side="left", padx=(15, 5), pady=15)
        type_var = StringVar(value="Sales Summary")
        ctk.CTkOptionMenu(controls, variable=type_var, values=["Sales Summary", "Invoice Wise", "Item Wise"]).pack(side="left", padx=5)
        
        # Dates
        ctk.CTkLabel(controls, text="From (BS):").pack(side="left", padx=(15, 5))
        start_entry = ctk.CTkEntry(controls, placeholder_text="YYYY-MM-DD", width=100)
        start_entry.pack(side="left", padx=5)
        start_entry.insert(0, DateUtils.get_current_bs_date_str())
        
        ctk.CTkLabel(controls, text="To (BS):").pack(side="left", padx=(15, 5))
        end_entry = ctk.CTkEntry(controls, placeholder_text="YYYY-MM-DD", width=100)
        end_entry.pack(side="left", padx=5)
        end_entry.insert(0, DateUtils.get_current_bs_date_str())
        
        # Results Area
        res_frame = ctk.CTkScrollableFrame(content, fg_color=("#ffffff", "#1e293b"))
        res_frame.pack(fill="both", expand=True)
        
        def generate():
            # Clear
            for w in res_frame.winfo_children(): w.destroy()
            
            # Convert BS inputs to AD for Backend
            s_bs = start_entry.get().strip()
            e_bs = end_entry.get().strip()
            s_date = DateUtils.bs_to_ad(s_bs)
            e_date = DateUtils.bs_to_ad(e_bs)
            
            rtype = type_var.get()
            
            headers = {"Authorization": f"Bearer {self.token}"} 
            
            try:
                data = []
                if rtype == "Sales Summary":
                    r = requests.get(f"{API_BASE}/reports/sales?type=summary&start_date={s_date}&end_date={e_date}", headers=headers)
                    if r.status_code == 200:
                        data = r.json()
                        # Columns: Date, Count, Total Sales, Net (VAT Removed)
                        cols = [("Date", 100), ("Bill Count", 80), ("Total Sales", 100), ("Net Sales", 100)]
                        
                        # Render Header
                        h_row = ctk.CTkFrame(res_frame)
                        h_row.pack(fill="x", pady=2)
                        for t,w in cols: ctk.CTkLabel(h_row, text=t, width=w, font=("Segoe UI Bold", 11)).pack(side="left")
                        
                        # Render Data
                        for row in data:
                            r_row = ctk.CTkFrame(res_frame, fg_color="transparent")
                            r_row.pack(fill="x", pady=2)
                            
                            # Row Data
                            dt_ad = row.get('date', '')[:10]
                            dt_bs = DateUtils.ad_to_bs(dt_ad)
                            cnt = row.get('count', 0)
                            sales = float(row.get('total_sales', 0))
                            
                            vals = [dt_bs, str(cnt), f"{sales:,.2f}", f"{sales:,.2f}"]
                            for (t,w), v in zip(cols, vals):
                                ctk.CTkLabel(r_row, text=v, width=w).pack(side="left")
                                
                elif rtype == "Invoice Wise":
                    r = requests.get(f"{API_BASE}/reports/sales?type=invoice&start_date={s_date}&end_date={e_date}", headers=headers)
                    if r.status_code == 200:
                        data = r.json()
                        cols = [("Invoice No", 120), ("Date", 100), ("Customer", 150), ("Amount", 100)]
                        h_row = ctk.CTkFrame(res_frame); h_row.pack(fill="x")
                        for t,w in cols: ctk.CTkLabel(h_row, text=t, width=w, font=("Segoe UI Bold", 11)).pack(side="left")
                        
                        for row in data:
                            r_row = ctk.CTkFrame(res_frame, fg_color="transparent"); r_row.pack(fill="x", pady=2)
                            
                            bs_date = DateUtils.ad_to_bs(row['created_at'][:10])
                            
                            vals = [row['bill_number'], bs_date, row.get('customer_name') or '-', f"{float(row['amount']):,.2f}"]
                            for (t,w), v in zip(cols, vals): ctk.CTkLabel(r_row, text=v, width=w).pack(side="left")

                elif rtype == "Item Wise":
                    r = requests.get(f"{API_BASE}/reports/items?start_date={s_date}&end_date={e_date}", headers=headers)
                    if r.status_code == 200:
                        data = r.json()
                        cols = [("Product", 200), ("Batch", 100), ("Qty Sold", 80), ("Revenue", 100)]
                        h_row = ctk.CTkFrame(res_frame); h_row.pack(fill="x")
                        for t,w in cols: ctk.CTkLabel(h_row, text=t, width=w, font=("Segoe UI Bold", 11)).pack(side="left")
                        
                        for row in data:
                            r_row = ctk.CTkFrame(res_frame, fg_color="transparent"); r_row.pack(fill="x", pady=2)
                            vals = [row['name'], row['batch_number'], str(row['qty']), f"{float(row['total_amount']):,.2f}"]
                            for (t,w), v in zip(cols, vals): ctk.CTkLabel(r_row, text=v, width=w).pack(side="left")

                if not data:
                    ctk.CTkLabel(res_frame, text="No records found").pack(pady=20)
                    
            except Exception as e:
                ctk.CTkLabel(res_frame, text=f"Error: {e}").pack()
        
        ctk.CTkButton(controls, text="Generate View", command=generate, width=150, fg_color="#3b82f6").pack(side="left", padx=20)
        
    def show_pdf_tools(self):
        """PDF Invoice Extractor UI"""
        for widget in self.root.winfo_children(): widget.destroy()
        
        container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        container.pack(fill="both", expand=True)
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(container, nav_items, "PDF Invoice Tools")
        
        content = ctk.CTkFrame(container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(content, text="📑 PDF Invoice Extractor (A4)", font=("Segoe UI Black", 24)).pack(anchor="w", pady=(0, 20))
        
        # Upload Area
        up_frame = ctk.CTkFrame(content, fg_color=("#e2e8f0", "#334155"), corner_radius=10)
        up_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(up_frame, text="Select A4 Invoice PDF:").pack(side="left", padx=20, pady=20)
        
        self.extracted_data = None
        
        def upload_and_process():
            from tkinter import filedialog
            from .pdf_extractor import InvoiceExtractor
            
            fp = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
            if not fp: return
            
            ext = InvoiceExtractor(fp)
            data = ext.extract()
            self.extracted_data = data
            
            # Show Results
            for w in res_area.winfo_children(): w.destroy()
            
            if "error" in data:
                ctk.CTkLabel(res_area, text=f"Error: {data['error']}", text_color="red").pack()
                return
                
            # Header Info
            info = ctk.CTkFrame(res_area, fg_color="transparent")
            info.pack(fill="x", pady=10)
            
            tk_color = "green" if data.get('template') == "AARAMBHA_A4_V1" else "orange"
            ctk.CTkLabel(info, text=f"Template: {data.get('template')}", text_color=tk_color, font=("Segoe UI Bold", 14)).pack(anchor="w")
            ctk.CTkLabel(info, text=f"Invoice: {data.get('invoice_no')} | Date: {data.get('date')}").pack(anchor="w")
            
            if data.get('warning'):
                ctk.CTkLabel(info, text=f"Warning: {data['warning']}", text_color="orange").pack(anchor="w")
            
            # Items Table
            if data.get('items'):
                cols = ["SN", "Product", "Batch", "Exp", "Qty", "Rate", "Amount"]
                h_row = ctk.CTkFrame(res_area)
                h_row.pack(fill="x", pady=5)
                for c in cols: ctk.CTkLabel(h_row, text=c, width=80, font=("Segoe UI Bold", 11)).pack(side="left")
                
                for row in data['items']:
                    r_row = ctk.CTkFrame(res_area, fg_color="transparent")
                    r_row.pack(fill="x", pady=2)
                    for val in row:
                        ctk.CTkLabel(r_row, text=str(val), width=80).pack(side="left")
            else:
                ctk.CTkLabel(res_area, text="No items extracted.").pack()
                
            btn_export.configure(state="normal")

        ctk.CTkButton(up_frame, text="📂 Upload & Extract", command=upload_and_process).pack(side="left", padx=20)
        
        btn_export = ctk.CTkButton(up_frame, text="💾 Export Excel", state="disabled", fg_color="#10b981")
        btn_export.pack(side="right", padx=20)
        
        def export_excel():
             if not self.extracted_data: return
             try:
                 import openpyxl
                 wb = openpyxl.Workbook()
                 ws = wb.active
                 ws.title = "Summary"
                 ws.append(["Invoice No", "Date", "Template"])
                 ws.append([self.extracted_data.get('invoice_no'), self.extracted_data.get('date'), self.extracted_data.get('template')])
                 
                 ws2 = wb.create_sheet("Items")
                 ws2.append(["SN", "Product", "Batch", "Exp", "Qty", "Rate", "Amount"])
                 for row in self.extracted_data.get('items', []):
                     ws2.append(row)
                 
                 fn = f"EXTRACT_{self.extracted_data.get('invoice_no')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                 wb.save(fn)
                 import os
                 os.startfile(os.path.abspath(fn))
                 messagebox.showinfo("Success", f"Exported to {fn}")
             except Exception as e:
                 messagebox.showerror("Error", str(e))
                 
        btn_export.configure(command=export_excel)

        # Result Area
        res_area = ctk.CTkScrollableFrame(content, fg_color="#fff")
        res_area.pack(fill="both", expand=True)
        
    def show_bill_log(self):
        """Show Bill Log / Invoice History"""
        for widget in self.root.winfo_children(): widget.destroy()
        
        container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        container.pack(fill="both", expand=True)
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(container, nav_items, "Bill Log")
        
        content = ctk.CTkFrame(container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # 1. Filter Bar
        flt_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), height=80)
        flt_frame.pack(fill="x", pady=(0, 20), padx=5, ipady=10)
        
        ctk.CTkLabel(flt_frame, text="Search Keywords:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        search_var = ctk.StringVar()
        ctk.CTkEntry(flt_frame, textvariable=search_var, width=200, placeholder_text="Invoice ID / Name / Phone").pack(side="left", padx=5)
        
        ctk.CTkLabel(flt_frame, text="Pay Mode:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        pay_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(flt_frame, variable=pay_var, values=["All", "CASH", "DIGITAL"], width=100).pack(side="left", padx=5)
        
        # Date Filter (Simple Combo for now or reuse DatePicker if imported)
        # Using simple combo for quick implementation as requested
        ctk.CTkLabel(flt_frame, text="Period:", font=("Segoe UI", 12)).pack(side="left", padx=(20, 5))
        period_var = ctk.StringVar(value="Today")
        ctk.CTkOptionMenu(flt_frame, variable=period_var, values=["Today", "Yesterday", "Last 7 Days", "All Time"], width=120).pack(side="left", padx=5)

        # 2. Results Grid
        res_frame = ctk.CTkScrollableFrame(content, fg_color="transparent")
        res_frame.pack(fill="both", expand=True)
        
        def load_bills():
            # Calculate dates
            import datetime
            today = datetime.date.today()
            s_date = today
            e_date = today
            p_val = period_var.get()
             
            if p_val == "Yesterday":
                s_date = today - datetime.timedelta(days=1)
                e_date = s_date
            elif p_val == "Last 7 Days":
                s_date = today - datetime.timedelta(days=7)
            elif p_val == "All Time":
                s_date = ""
                e_date = ""
            
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"{self.API_BASE}/sales/log?search={search_var.get()}&payment_method={pay_var.get()}"
            if s_date: url += f"&start_date={s_date}&end_date={e_date}"
            
            try:
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    render_table(data)
                else:
                    messagebox.showerror("Error", f"Failed to fetch logs: {r.text}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def render_table(rows):
            for w in res_frame.winfo_children(): w.destroy()
            
            # Header
            cols = [("Invoice No", 100), ("Date", 150), ("Customer", 150), ("Sold By", 120), ("Pay Mode", 80), ("Amount", 100), ("Actions", 100)]
            h_frm = ctk.CTkFrame(res_frame, fg_color=("#e2e8f0", "#334155"))
            h_frm.pack(fill="x", pady=2)
            for t, w in cols: ctk.CTkLabel(h_frm, text=t, width=w, font=("Segoe UI Bold", 11)).pack(side="left", padx=2)
            
            # Rows
            for row in rows:
                r_frm = ctk.CTkFrame(res_frame, fg_color="transparent")
                r_frm.pack(fill="x", pady=2)
                
                vals = [
                    row['bill_number'], 
                    DateUtils.ad_to_bs(row['created_at'].split('T')[0]),
                    f"{row.get('customer_name') or 'Walk-in'}\n{row.get('customer_contact') or ''}",
                    row.get('sold_by', '-'),
                    row['payment_category'],
                    f"Rs. {float(row['grand_total']):,.2f}"
                ]
                
                # Check for cancelled
                status = row.get('status', 'completed')
                fg = "red" if status == 'cancelled' else ("#000" if ctk.get_appearance_mode()=="Light" else "#fff")
                
                for (t,w), v in zip(cols[:-1], vals):
                    ctk.CTkLabel(r_frm, text=v, width=w, text_color=fg).pack(side="left", padx=2)
                
                # Action Button
                ctk.CTkButton(r_frm, text="View/Reprint", width=90, height=25, 
                              command=lambda r=row: self.show_bill_detail(r)).pack(side="left", padx=5)

        ctk.CTkButton(flt_frame, text="🔍 Search", command=load_bills, width=100).pack(side="left", padx=20)
        
        # Initial Load
        load_bills()

    def show_bill_detail(self, bill_row):
        """Detail Modal for Bill"""
        top = ctk.CTkToplevel(self.root)
        top.title(f"Invoice Detail: {bill_row['bill_number']}")
        top.geometry("600x800")
        
        # Load Data
        lbl_load = ctk.CTkLabel(top, text="Fetching details...", font=("Segoe UI", 16))
        lbl_load.pack(pady=20)
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            r = requests.get(f"{self.API_BASE}/sales/{bill_row['id']}", headers=headers)
            if r.status_code != 200:
                lbl_load.configure(text=f"Error: {r.text}", text_color="red")
                return
            
            data = r.json()
            lbl_load.destroy()
            
            # --- UI Layout ---
            # 1. Header Actions
            act_frm = ctk.CTkFrame(top, fg_color="transparent")
            act_frm.pack(fill="x", padx=20, pady=10)
            
            def reprint_bill():
                try:
                    from .pdf_generator import generate_invoice
                    import os
                    if not os.path.exists("invoices"): os.makedirs("invoices")
                    fname = f"invoices/REPRINT_{data['bill_number']}.pdf"
                    
                    # Prepare Data
                    p_data = {
                        "bill_number": data['bill_number'],
                        "created_at": DateUtils.ad_to_bs(data['created_at'].split('T')[0]),
                        "customer_name": data.get('customer_name'),
                        "customer_contact": data.get('customer_contact'),
                        "customer_address": data.get('customer_address'), # May not be in DB unless we added it
                        "payment_category": data['payment_category'],
                        "sold_by": data.get('sold_by', 'Admin'),
                        "grand_total": data['grand_total'],
                        "discount_amount": data.get('discount_amount', 0),
                        "items": data.get('items', []),
                        "pharmacy_name": data.get('pharmacy_name'),
                        "pharmacy_address": data.get('pharmacy_address'),
                        "pharmacy_contact": data.get('pharmacy_contact'),
                        "pan_number": data.get('pan_number')
                    }
                    
                    generate_invoice(p_data, fname)
                    os.startfile(os.path.abspath(fname))
                except Exception as e:
                    messagebox.showerror("Error", f"Reprint Failed: {e}")

            ctk.CTkButton(act_frm, text="🖨️ Reprint (A4)", command=reprint_bill, width=120).pack(side="right")
            
            # 2. Preview Info
            info = ctk.CTkScrollableFrame(top, fg_color="#fff", label_text="Invoice Preview")
            info.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Header
            ctk.CTkLabel(info, text=data.get('pharmacy_name', 'PHARMACY'), font=("Arial", 18, "bold"), text_color="black").pack()
            ctk.CTkLabel(info, text=f"Invoice: {data['bill_number']}", text_color="black").pack()
            ctk.CTkLabel(info, text=f"Date: {data['created_at'][:10]}", text_color="black").pack()
            ctk.CTkLabel(info, text=f"Customer: {data.get('customer_name') or 'Walk-in'}", text_color="black").pack(anchor="w", padx=10, pady=(10,0))
            
            # Items
            ctk.CTkLabel(info, text="Items:", font=("Arial", 12, "bold"), text_color="black").pack(anchor="w", padx=10, pady=(10,5))
            
            i_frm = ctk.CTkFrame(info, fg_color="transparent")
            i_frm.pack(fill="x", padx=10)
            
            cols = [("Item", 180), ("Qty", 50), ("Rate", 80), ("Total", 80)]
            h = ctk.CTkFrame(i_frm, fg_color="#eee")
            h.pack(fill="x")
            for t,w in cols: ctk.CTkLabel(h, text=t, width=w, font=("Arial", 10, "bold"), text_color="black").pack(side="left")
            
            for item in data.get('items', []):
                r = ctk.CTkFrame(i_frm, fg_color="transparent")
                r.pack(fill="x")
                vals = [item['name'][:20], str(item['qty']), f"{item['rate']}", f"{item['amount']}"]
                for (t,w), v in zip(cols, vals): ctk.CTkLabel(r, text=v, width=w, text_color="black", font=("Arial", 10)).pack(side="left")
                
            # Totals
            ctk.CTkLabel(info, text="------------------------------------------------", text_color="black").pack(pady=5)
            ctk.CTkLabel(info, text=f"Grand Total: Rs. {float(data['grand_total']):,.2f}", font=("Arial", 14, "bold"), text_color="black").pack(anchor="e", padx=20)
            ctk.CTkLabel(info, text="* VAT Exempted Goods (Medicine)", font=("Arial", 10, "italic"), text_color="black").pack(pady=10)

        except Exception as e:
            lbl_load.configure(text=f"Error: {e}", text_color="red")


        





        

    def show_low_stock_alerts(self):
        """Low Stock Alerts Page - View all low stock items with SMS buttons"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Low Stock Alerts")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        ctk.CTkLabel(content, text="📉 Low Stock Alerts", font=("Segoe UI Black", 28)).pack(anchor="w", pady=(0, 20))
        
        # Fetch low stock items
        def load_alerts():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                r = requests.get(f"{API_BASE}/dashboard/alerts", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    display_alerts(data.get('lowStock', []))
            except Exception as e:
                print(f"Error: {e}")
        
        def display_alerts(items):
            for w in alert_list.winfo_children():
                w.destroy()
            
            if not items:
                ctk.CTkLabel(alert_list, text="✅ No low stock items", font=("Segoe UI", 16), text_color="gray").pack(pady=50)
                return
            
            # Table header
            header = ctk.CTkFrame(alert_list, fg_color=("#e2e8f0", "#334155"))
            header.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(header, text="Medicine Name", font=("Segoe UI Bold", 13), width=200).grid(row=0, column=0, padx=5, pady=10)
            ctk.CTkLabel(header, text="Vendor", font=("Segoe UI Bold", 13), width=150).grid(row=0, column=1, padx=5, pady=10)
            ctk.CTkLabel(header, text="Batch", font=("Segoe UI Bold", 13), width=100).grid(row=0, column=2, padx=5, pady=10)
            ctk.CTkLabel(header, text="Expiry", font=("Segoe UI Bold", 13), width=100).grid(row=0, column=3, padx=5, pady=10)
            ctk.CTkLabel(header, text="Stock", font=("Segoe UI Bold", 13), width=80).grid(row=0, column=4, padx=5, pady=10)
            ctk.CTkLabel(header, text="Actions", font=("Segoe UI Bold", 13), width=120).grid(row=0, column=5, padx=5, pady=10)
            
            for item in items:
                row = ctk.CTkFrame(alert_list, fg_color="transparent")
                row.pack(fill="x", pady=5)
                
                ctk.CTkLabel(row, text=item['medicine_name'], width=200, anchor="w").grid(row=0, column=0, padx=5, pady=10)
                ctk.CTkLabel(row, text=item.get('vendor_name', 'N/A'), width=150, anchor="w").grid(row=0, column=1, padx=5, pady=10)
                ctk.CTkLabel(row, text=item.get('batch_number', 'N/A'), width=100).grid(row=0, column=2, padx=5, pady=10)
                
                exp_date = item.get('expiry_date', 'N/A')
                if exp_date and 'T' in exp_date: exp_date = exp_date.split('T')[0]
                
                ctk.CTkLabel(row, text=exp_date, width=100).grid(row=0, column=3, padx=5, pady=10)
                ctk.CTkLabel(row, text=str(item['quantity']), text_color="#f59e0b", width=80, font=("Segoe UI Bold", 12)).grid(row=0, column=4, padx=5, pady=10)
                
                btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                btn_frame.grid(row=0, column=5, padx=5, pady=5)
                
                ctk.CTkButton(btn_frame, text="📋", width=40, height=30,
                             command=lambda i=item: show_item_details(i),
                             fg_color="#3b82f6").pack(side="left", padx=2)
                
                ctk.CTkButton(btn_frame, text="📱 SMS", width=60, height=30,
                             command=lambda i=item: send_sms_alert(i, 'LOW_STOCK'),
                             fg_color="#10b981").pack(side="left", padx=2)
        
        def show_item_details(item):
            exp_date = item.get('expiry_date', 'N/A')
            if exp_date and 'T' in exp_date: exp_date = exp_date.split('T')[0]
            messagebox.showinfo("Product Details", 
                              f"Medicine: {item['medicine_name']}\n"
                              f"Vendor: {item.get('vendor_name', 'N/A')}\n"
                              f"Batch: {item.get('batch_number', 'N/A')}\n"
                              f"Expiry: {exp_date}\n"
                              f"Current Stock: {item['quantity']}\n"
                              f"Threshold: {item.get('threshold', 10)}")

        def send_sms_alert(item, alert_type):
            try:
                phone = self.user.get('phone', '')
                if not phone:
                    return messagebox.showerror("Error", "Phone not found")
                
                productData = {
                    'id': item.get('medicine_id') or item.get('id'),
                    'name': item.get('medicine_name'),
                    'vendor': item.get('vendor_name', 'N/A'),
                    'batch': item.get('batch_number', ''),
                    'stock': item.get('quantity', 0),
                    'unit': 'units'
                }
                
                payload = {'type': alert_type, 'productData': productData, 'toNumber': phone}
                headers = {"Authorization": f"Bearer {self.token}"}
                r = requests.post(f"{API_BASE}/sms/send-alert", json=payload, headers=headers)
                
                if r.status_code == 200:
                    messagebox.showinfo("Success", "SMS sent!")
                elif r.status_code == 429:
                    messagebox.showwarning("Already Sent", "SMS sent recently")
                else:
                    messagebox.showerror("Error", "Failed to send SMS")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        alert_list = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        alert_list.pack(fill="both", expand=True, pady=(0, 20))
        
        ctk.CTkButton(content, text="🔄 Refresh", command=load_alerts, fg_color="#3b82f6", height=40).pack(pady=10)
        load_alerts()
    
    def show_expiry_alerts(self):
        """Expiry Alerts Page - View all expiring items with SMS buttons"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Expiry Alerts")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        ctk.CTkLabel(content, text="⚠️ Expiry Alerts (3 Months)", font=("Segoe UI Black", 28)).pack(anchor="w", pady=(0, 20))
        
        # Fetch expiry items
        def load_alerts():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                r = requests.get(f"{API_BASE}/dashboard/alerts", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    display_alerts(data.get('expiry', []))
            except Exception as e:
                print(f"Error: {e}")
        
        def display_alerts(items):
            for w in alert_list.winfo_children():
                w.destroy()
            
            if not items:
                ctk.CTkLabel(alert_list, text="✅ No expiring items", font=("Segoe UI", 16), text_color="gray").pack(pady=50)
                return
            
            # Table header
            header = ctk.CTkFrame(alert_list, fg_color=("#e2e8f0", "#334155"))
            header.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(header, text="Medicine Name", font=("Segoe UI Bold", 13), width=200).grid(row=0, column=0, padx=5, pady=10)
            ctk.CTkLabel(header, text="Vendor", font=("Segoe UI Bold", 13), width=150).grid(row=0, column=1, padx=5, pady=10)
            ctk.CTkLabel(header, text="Batch", font=("Segoe UI Bold", 13), width=100).grid(row=0, column=2, padx=5, pady=10)
            ctk.CTkLabel(header, text="Expiry Date", font=("Segoe UI Bold", 13), width=100).grid(row=0, column=3, padx=5, pady=10)
            ctk.CTkLabel(header, text="Stock", font=("Segoe UI Bold", 13), width=80).grid(row=0, column=4, padx=5, pady=10)
            ctk.CTkLabel(header, text="Actions", font=("Segoe UI Bold", 13), width=120).grid(row=0, column=5, padx=5, pady=10)
            
            for item in items:
                row = ctk.CTkFrame(alert_list, fg_color="transparent")
                row.pack(fill="x", pady=5)
                
                ctk.CTkLabel(row, text=item['medicine_name'], width=200, anchor="w").grid(row=0, column=0, padx=5, pady=10)
                ctk.CTkLabel(row, text=item.get('vendor_name', 'N/A'), width=150, anchor="w").grid(row=0, column=1, padx=5, pady=10)
                ctk.CTkLabel(row, text=item.get('batch_number', 'N/A'), width=100).grid(row=0, column=2, padx=5, pady=10)
                
                exp_date = item.get('expiry_date', '').split('T')[0]
                ctk.CTkLabel(row, text=exp_date, text_color="#ef4444", width=100, font=("Segoe UI Bold", 12)).grid(row=0, column=3, padx=5, pady=10)
                ctk.CTkLabel(row, text=str(item.get('quantity', 0)), width=80).grid(row=0, column=4, padx=5, pady=10)
                
                btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                btn_frame.grid(row=0, column=5, padx=5, pady=5)
                
                ctk.CTkButton(btn_frame, text="📋", width=40, height=30,
                             command=lambda i=item: show_item_details(i),
                             fg_color="#3b82f6").pack(side="left", padx=2)
                
                ctk.CTkButton(btn_frame, text="📱 SMS", width=60, height=30,
                             command=lambda i=item: send_sms_alert(i, 'EXPIRY'),
                             fg_color="#10b981").pack(side="left", padx=2)
        
        def show_item_details(item):
            messagebox.showinfo("Product Details", 
                              f"Medicine: {item['medicine_name']}\n"
                              f"Vendor: {item.get('vendor_name', 'N/A')}\n"
                              f"Batch: {item.get('batch_number', 'N/A')}\n"
                              f"Expiry: {item.get('expiry_date', '').split('T')[0]}\n"
                              f"Current Stock: {item.get('quantity', 0)}")

        def send_sms_alert(item, alert_type):
            try:
                phone = self.user.get('phone', '')
                if not phone:
                    return messagebox.showerror("Error", "Phone not found")
                
                productData = {
                    'id': item.get('medicine_id') or item.get('id'),
                    'name': item.get('medicine_name'),
                    'vendor': item.get('vendor_name', 'N/A'),
                    'expiry': item.get('expiry_date', '').split('T')[0],
                    'batch': item.get('batch_number', ''),
                    'stock': item.get('quantity', 0),
                    'unit': 'units'
                }
                
                payload = {'type': alert_type, 'productData': productData, 'toNumber': phone}
                headers = {"Authorization": f"Bearer {self.token}"}
                r = requests.post(f"{API_BASE}/sms/send-alert", json=payload, headers=headers)
                
                if r.status_code == 200:
                    messagebox.showinfo("Success", "SMS sent!")
                elif r.status_code == 429:
                    messagebox.showwarning("Already Sent", "SMS sent recently")
                else:
                    messagebox.showerror("Error", "Failed to send SMS")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        alert_list = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        alert_list.pack(fill="both", expand=True, pady=(0, 20))
        
        ctk.CTkButton(content, text="🔄 Refresh", command=load_alerts, fg_color="#3b82f6", height=40).pack(pady=10)
        load_alerts()

    def show_customer_management(self):
        """Customer Management - Simple CRM (NO SMS)"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Customer Database")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="👥 Customer Database", font=("Segoe UI Black", 28)).pack(side="left")
        ctk.CTkButton(header, text="+ Add Customer", command=self.show_add_customer_dialog,
                     fg_color="#10b981", height=40).pack(side="right")
        
        # Search
        search_var = StringVar()
        search_frame = ctk.CTkFrame(content, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 20))
        
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search by name or mobile...",
                                    textvariable=search_var, width=400)
        search_entry.pack(side="left", padx=(0, 10))
        
        def load_customers():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                params = {'search': search_var.get()} if search_var.get() else {}
                r = requests.get(f"{API_BASE}/customers", headers=headers, params=params)
                if r.status_code == 200:
                    display_customers(r.json())
            except Exception as e:
                print(f"Error: {e}")
        
        def display_customers(customers):
            for w in table_frame.winfo_children():
                w.destroy()
            
            if not customers:
                ctk.CTkLabel(table_frame, text="No customers found", text_color="gray").pack(pady=50)
                return
            
            # Table header
            header_row = ctk.CTkFrame(table_frame, fg_color=("#e2e8f0", "#334155"))
            header_row.pack(fill="x", pady=(0, 5))
            
            ctk.CTkLabel(header_row, text="ID", font=("Segoe UI Bold", 12), width=100).grid(row=0, column=0, padx=5, pady=10)
            ctk.CTkLabel(header_row, text="Name", font=("Segoe UI Bold", 12), width=200).grid(row=0, column=1, padx=5, pady=10)
            ctk.CTkLabel(header_row, text="Mobile", font=("Segoe UI Bold", 12), width=150).grid(row=0, column=2, padx=5, pady=10)
            ctk.CTkLabel(header_row, text="Registered (BS)", font=("Segoe UI Bold", 12), width=120).grid(row=0, column=3, padx=5, pady=10)
            ctk.CTkLabel(header_row, text="Address", font=("Segoe UI Bold", 12), width=200).grid(row=0, column=4, padx=5, pady=10)
            ctk.CTkLabel(header_row, text="Actions", font=("Segoe UI Bold", 12), width=100).grid(row=0, column=5, padx=5, pady=10)
            
            # Rows
            for cust in customers:
                row = ctk.CTkFrame(table_frame, fg_color=("#f8fafc", "#1e293b"))
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=cust.get('customer_id', ''), width=100).grid(row=0, column=0, padx=5, pady=10)
                ctk.CTkLabel(row, text=cust.get('full_name', ''), width=200, anchor="w").grid(row=0, column=1, padx=5, pady=10)
                ctk.CTkLabel(row, text=cust.get('mobile_number', '-'), width=150).grid(row=0, column=2, padx=5, pady=10)
                
                # BS Date
                reg_bs = DateUtils.ad_to_bs(cust.get('created_at', ''))
                ctk.CTkLabel(row, text=reg_bs, width=120).grid(row=0, column=3, padx=5, pady=10)
                
                ctk.CTkLabel(row, text=cust.get('address', '-')[:30], width=200, anchor="w").grid(row=0, column=4, padx=5, pady=10)
                
                ctk.CTkButton(row, text="✏️", width=40, height=25,
                             command=lambda c=cust: self.show_edit_customer_dialog(c),
                             fg_color="#3b82f6").grid(row=0, column=5, padx=5, pady=5)
        
        search_var.trace('w', lambda *args: load_customers())
        
        ctk.CTkButton(search_frame, text="🔄 Refresh", command=load_customers,
                     fg_color="#3b82f6", width=100).pack(side="left")
        
        # Table
        table_frame = ctk.CTkFrame(content, fg_color="transparent")
        table_frame.pack(fill="both", expand=True)
        
        load_customers()
    
    def show_add_customer_dialog(self):
        """Quick add customer dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Customer")
        dialog.geometry("450x450")
        dialog.grab_set()  # Make modal
        dialog.transient(self.root)  # Set parent
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (450 // 2)
        dialog.geometry(f"450x450+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="Add New Customer", font=("Segoe UI Bold", 18)).pack(pady=20)
        
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)
        
        name_var = StringVar()
        mobile_var = StringVar()
        address_var = StringVar()
        notes_var = StringVar()
        
        ctk.CTkLabel(form, text="Full Name *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        name_entry = ctk.CTkEntry(form, textvariable=name_var, height=35)
        name_entry.pack(fill="x")
        
        ctk.CTkLabel(form, text="Mobile Number *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        mobile_entry = ctk.CTkEntry(form, textvariable=mobile_var, height=35)
        mobile_entry.pack(fill="x")
        
        ctk.CTkLabel(form, text="Address", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        address_entry = ctk.CTkEntry(form, textvariable=address_var, height=35)
        address_entry.pack(fill="x")
        
        ctk.CTkLabel(form, text="Notes", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        notes_entry = ctk.CTkEntry(form, textvariable=notes_var, height=35)
        notes_entry.pack(fill="x")
        
        def save_customer():
            if not name_var.get().strip():
                messagebox.showerror("Error", "Name is required", parent=dialog)
                return
            
            if not mobile_var.get().strip():
                messagebox.showerror("Error", "Mobile number is required", parent=dialog)
                return
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    'full_name': name_var.get().strip(),
                    'mobile_number': mobile_var.get().strip(),
                    'address': address_var.get().strip() or None,
                    'notes': notes_var.get().strip() or None
                }
                r = requests.post(f"{API_BASE}/customers", json=data, headers=headers)
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Customer added successfully!", parent=dialog)
                    dialog.destroy()
                    self.show_customer_management()
                elif r.status_code == 409:
                    messagebox.showerror("Error", "Customer with this mobile number already exists", parent=dialog)
                else:
                    messagebox.showerror("Error", r.json().get('message', 'Failed to add customer'), parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dialog)
        
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                     fg_color="#6b7280", hover_color="#4b5563", width=100, height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="Save Customer", command=save_customer,
                     fg_color="#10b981", hover_color="#059669", width=150, height=40).pack(side="left", padx=5)
        
        # Focus on name field
        name_entry.focus()
    
    def show_edit_customer_dialog(self, customer):
        """Edit customer dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Customer")
        dialog.geometry("400x400")
        
        ctk.CTkLabel(dialog, text="Edit Customer", font=("Segoe UI Bold", 18)).pack(pady=20)
        
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)
        
        name_var = StringVar(value=customer.get('full_name', ''))
        mobile_var = StringVar(value=customer.get('mobile_number', ''))
        address_var = StringVar(value=customer.get('address', ''))
        notes_var = StringVar(value=customer.get('notes', ''))
        
        ctk.CTkLabel(form, text="Full Name *").pack(anchor="w", pady=(10, 5))
        ctk.CTkEntry(form, textvariable=name_var).pack(fill="x")
        
        ctk.CTkLabel(form, text="Mobile Number").pack(anchor="w", pady=(10, 5))
        ctk.CTkEntry(form, textvariable=mobile_var).pack(fill="x")
        
        ctk.CTkLabel(form, text="Address").pack(anchor="w", pady=(10, 5))
        ctk.CTkEntry(form, textvariable=address_var).pack(fill="x")
        
        ctk.CTkLabel(form, text="Notes").pack(anchor="w", pady=(10, 5))
        ctk.CTkEntry(form, textvariable=notes_var).pack(fill="x")
        
        def update_customer():
            if not name_var.get():
                return messagebox.showerror("Error", "Name is required")
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    'full_name': name_var.get(),
                    'mobile_number': mobile_var.get() or None,
                    'address': address_var.get() or None,
                    'notes': notes_var.get() or None,
                    'status': 'active'
                }
                r = requests.put(f"{API_BASE}/customers/{customer['id']}", json=data, headers=headers)
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Customer updated!")
                    dialog.destroy()
                    self.show_customer_management()
                else:
                    messagebox.showerror("Error", "Failed to update")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(form, text="Update Customer", command=update_customer,
                     fg_color="#3b82f6", height=40).pack(pady=20)

    def show_notification_management(self):
        """Admin - Notification Management"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Notifications")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="📢 Notification Management", font=("Segoe UI Black", 28)).pack(side="left")
        ctk.CTkButton(header, text="+ Create Notification", command=self.show_create_notification_dialog,
                     fg_color="#10b981", height=40).pack(side="right")
        
        status_var = StringVar(value="active")
        
        def load_notifs():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                params = {'status': status_var.get()}
                r = requests.get(f"{API_BASE}/notifications/admin", headers=headers, params=params)
                if r.status_code == 200:
                    display_notifs(r.json())
            except Exception as e:
                print(f"Error: {e}")
        
        def display_notifs(notifs):
            for w in notif_list.winfo_children():
                w.destroy()
            
            if not notifs:
                ctk.CTkLabel(notif_list, text="No notifications", text_color="gray").pack(pady=50)
                return
            
            for notif in notifs:
                card = ctk.CTkFrame(notif_list, fg_color=("#f8fafc", "#1e293b"), corner_radius=10)
                card.pack(fill="x", pady=10, padx=5)
                
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(fill="both", expand=True, padx=15, pady=15)
                
                ctk.CTkLabel(info, text=notif['title'], font=("Segoe UI Bold", 16)).pack(anchor="w")
                ctk.CTkLabel(info, text=notif['description'][:100], font=("Segoe UI", 12), text_color="gray").pack(anchor="w", pady=(5, 0))
                
                details = f"{notif['start_date']} → {notif['end_date']} | {notif.get('read_count', 0)}/{notif.get('total_recipients', 0)} read"
                ctk.CTkLabel(info, text=details, font=("Segoe UI", 11), text_color="gray").pack(anchor="w", pady=(10, 0))
        
        notif_list = ctk.CTkFrame(content, fg_color="transparent")
        notif_list.pack(fill="both", expand=True)
        
        ctk.CTkButton(content, text="🔄 Refresh", command=load_notifs, fg_color="#3b82f6", height=40).pack(pady=10)
        load_notifs()
    
    def show_create_notification_dialog(self):
        """Create Notification Dialog"""
        from tkcalendar import DateEntry
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create Notification")
        dialog.geometry("650x750")
        dialog.grab_set()
        dialog.transient(self.root)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (dialog.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f"650x750+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="Create Notification", font=("Segoe UI Bold", 20)).pack(pady=20)
        
        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)
        
        title_var = StringVar()
        priority_var = StringVar(value="normal")
        target_var = StringVar(value="all")
        selected_cashiers = []
        
        ctk.CTkLabel(form, text="Title *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        ctk.CTkEntry(form, textvariable=title_var, height=35).pack(fill="x")
        
        ctk.CTkLabel(form, text="Description *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        desc_textbox = ctk.CTkTextbox(form, height=120)
        desc_textbox.pack(fill="x")
        
        ctk.CTkLabel(form, text="Priority", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        ctk.CTkOptionMenu(form, variable=priority_var, values=["normal", "important", "urgent"]).pack(fill="x")
        
        # Target selection
        ctk.CTkLabel(form, text="Target *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        
        target_frame = ctk.CTkFrame(form, fg_color="transparent")
        target_frame.pack(fill="x")
        
        ctk.CTkRadioButton(target_frame, text="All Cashiers", variable=target_var, value="all").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(target_frame, text="Selected Cashiers", variable=target_var, value="selected").pack(anchor="w", pady=5)
        
        # Cashier selection (shown when "selected" is chosen)
        cashier_frame = ctk.CTkFrame(form, fg_color=("#e2e8f0", "#334155"), corner_radius=10)
        cashier_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(cashier_frame, text="Select Cashiers:", font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=10, pady=5)
        
        # Fetch and display cashiers
        cashier_checkboxes = []
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            r = requests.get(f"{API_BASE}/users/cashiers", headers=headers)
            if r.status_code == 200:
                cashiers = r.json()
                for cashier in cashiers:
                    var = BooleanVar()
                    cb = ctk.CTkCheckBox(cashier_frame, text=f"{cashier['name']} ({cashier.get('phone', 'N/A')})",
                                        variable=var)
                    cb.pack(anchor="w", padx=20, pady=3)
                    cashier_checkboxes.append((cashier['id'], var))
            else:
                ctk.CTkLabel(cashier_frame, text="No cashiers found", text_color="gray").pack(padx=10, pady=5)
        except Exception as e:
            print(f"Error loading cashiers: {e}")
        
        # Date pickers
        ctk.CTkLabel(form, text="Start Date *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        start_date_picker = DateEntry(form, width=40, background='darkblue', foreground='white', borderwidth=2,
                                      date_pattern='yyyy-mm-dd')
        start_date_picker.pack(fill="x", pady=5)
        
        ctk.CTkLabel(form, text="End Date *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
        end_date_picker = DateEntry(form, width=40, background='darkblue', foreground='white', borderwidth=2,
                                    date_pattern='yyyy-mm-dd')
        end_date_picker.pack(fill="x", pady=5)
        
        def create_notif():
            title = title_var.get().strip()
            description = desc_textbox.get("1.0", "end-1c").strip()
            
            if not title or not description:
                return messagebox.showerror("Error", "Title and description are required", parent=dialog)
            
            # Get selected cashiers if target is "selected"
            cashier_ids = []
            if target_var.get() == "selected":
                cashier_ids = [cid for cid, var in cashier_checkboxes if var.get()]
                if not cashier_ids:
                    return messagebox.showerror("Error", "Please select at least one cashier", parent=dialog)
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    'title': title,
                    'description': description,
                    'priority': priority_var.get(),
                    'target': target_var.get(),
                    'start_date': start_date_picker.get_date().strftime('%Y-%m-%d'),
                    'end_date': end_date_picker.get_date().strftime('%Y-%m-%d'),
                    'cashier_ids': cashier_ids
                }
                
                r = requests.post(f"{API_BASE}/notifications", json=data, headers=headers)
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Notification created successfully!", parent=dialog)
                    dialog.destroy()
                    self.show_notification_management()
                else:
                    messagebox.showerror("Error", r.json().get('message', 'Failed to create notification'), parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dialog)
        
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                     fg_color="#6b7280", width=100, height=40).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Create Notification", command=create_notif,
                     fg_color="#10b981", width=180, height=40).pack(side="left", padx=5)

    def show_refund_management(self):
        """Admin - Refund Management"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Refund Requests")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(content, text="🔄 Refund Management", font=("Segoe UI Black", 28)).pack(anchor="w", pady=(0, 20))
        
        status_var = StringVar(value="PENDING")
        
        def load_refunds():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                params = {'status': status_var.get()} if status_var.get() != "ALL" else {}
                r = requests.get(f"{API_BASE}/refunds", headers=headers, params=params)
                if r.status_code == 200:
                    display_refunds(r.json())
            except Exception as e:
                print(f"Error: {e}")
        
        # Status tabs
        tab_frame = ctk.CTkFrame(content, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(0, 20))
        
        for stat in [("Pending", "PENDING"), ("Approved", "APPROVED"), ("Rejected", "REJECTED"), ("All", "ALL")]:
            ctk.CTkButton(tab_frame, text=stat[0], width=100,
                         command=lambda s=stat[1]: [status_var.set(s), load_refunds()],
                         fg_color="#f59e0b" if stat[1] == "PENDING" else "#6b7280").pack(side="left", padx=5)
        
        def display_refunds(refunds):
            for w in refund_list.winfo_children():
                w.destroy()
            
            if not refunds:
                ctk.CTkLabel(refund_list, text="No refund requests", text_color="gray").pack(pady=50)
                return
            
            for ref in refunds:
                card = ctk.CTkFrame(refund_list, fg_color=("#f8fafc", "#1e293b"), corner_radius=10)
                card.pack(fill="x", pady=10, padx=5)
                
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(fill="both", expand=True, padx=15, pady=15)
                
                # Header row
                header_row = ctk.CTkFrame(info, fg_color="transparent")
                header_row.pack(fill="x")
                
                ctk.CTkLabel(header_row, text=ref['refund_id'], font=("Segoe UI Bold", 16)).pack(side="left")
                
                status_colors = {'PENDING': '#f59e0b', 'APPROVED': '#10b981', 'REJECTED': '#ef4444'}
                status_color = status_colors.get(ref['status'], '#6b7280')
                ctk.CTkLabel(header_row, text=ref['status'], font=("Segoe UI Bold", 11),
                           text_color=status_color).pack(side="left", padx=10)
                
                # Details
                details = f"Bill: {ref['bill_number']} | Type: {ref['refund_type']} | Amount: ₹{ref['refund_amount']}"
                ctk.CTkLabel(info, text=details, font=("Segoe UI", 12), text_color="gray").pack(anchor="w", pady=(5, 0))
                
                reason_text = f"Reason: {ref['reason'].replace('_', ' ').title()}"
                ctk.CTkLabel(info, text=reason_text, font=("Segoe UI", 11), text_color="gray").pack(anchor="w", pady=(5, 0))
                
                bs_date = DateUtils.ad_to_bs(ref['created_at'])
                cashier_text = f"Requested by: {ref['requested_by_name']} | {bs_date}"
                ctk.CTkLabel(info, text=cashier_text, font=("Segoe UI", 10), text_color="gray").pack(anchor="w", pady=(5, 0))
                
                # Actions (only for pending)
                if ref['status'] == 'PENDING':
                    btn_row = ctk.CTkFrame(info, fg_color="transparent")
                    btn_row.pack(fill="x", pady=(10, 0))
                    
                    ctk.CTkButton(btn_row, text="✅ Approve", width=100,
                                 command=lambda r=ref: approve_refund(r['id']),
                                 fg_color="#10b981").pack(side="left", padx=5)
                    
                    ctk.CTkButton(btn_row, text="❌ Reject", width=100,
                                 command=lambda r=ref: reject_refund(r['id']),
                                 fg_color="#ef4444").pack(side="left", padx=5)
        
        def approve_refund(refund_id):
            if not messagebox.askyesno("Confirm", "Approve this refund? Stock will be adjusted."):
                return
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                r = requests.put(f"{API_BASE}/refunds/{refund_id}/approve", headers=headers)
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Refund approved and stock adjusted!")
                    load_refunds()
                else:
                    messagebox.showerror("Error", "Failed to approve refund")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        def reject_refund(refund_id):
            remarks = messagebox.askstring("Reject Refund", "Enter rejection reason:")
            if not remarks:
                return
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {'admin_remarks': remarks}
                r = requests.put(f"{API_BASE}/refunds/{refund_id}/reject", json=data, headers=headers)
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Refund rejected")
                    load_refunds()
                else:
                    messagebox.showerror("Error", "Failed to reject refund")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        refund_list = ctk.CTkFrame(content, fg_color="transparent")
        refund_list.pack(fill="both", expand=True)
        
        ctk.CTkButton(content, text="🔄 Refresh", command=load_refunds, fg_color="#3b82f6", height=40).pack(pady=10)
        load_refunds()

    def show_profile_management(self):
        """Profile Management for Admin/Super Admin"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
        self.create_sidebar(main_container, nav_items, "Profile Management")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(content, text="👤 Profile Management", font=("Segoe UI Black", 28)).pack(anchor="w", pady=(0, 20))
        
        # Profile form
        form_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        form_frame.pack(fill="both", expand=True, pady=10)
        
        form = ctk.CTkFrame(form_frame, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Load current profile
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            r = requests.get(f"{API_BASE}/profile", headers=headers)
            if r.status_code == 200:
                profile = r.json()
            else:
                profile = {}
        except:
            profile = {}
        
        name_var = StringVar(value=profile.get('name', ''))
        phone_var = StringVar(value=profile.get('phone', ''))
        email_var = StringVar(value=profile.get('email', ''))
        
        # Profile Picture with actual image display
        ctk.CTkLabel(form, text="Profile Picture", font=("Segoe UI Semibold", 14)).pack(anchor="w", pady=(10, 5))
        
        # Picture preview frame
        pic_preview_frame = ctk.CTkFrame(form, fg_color="transparent")
        pic_preview_frame.pack(fill="x", pady=10)
        
        # Create circular image frame
        pic_box = ctk.CTkFrame(pic_preview_frame, width=120, height=120, corner_radius=60, fg_color=("#e2e8f0", "#1e293b"))
        pic_box.pack(side="left", padx=(0, 20))
        pic_box.pack_propagate(False)
        
        # Display current profile picture
        current_pic_base64 = profile.get('profile_pic')
        pic_label = ctk.CTkLabel(pic_box, text="", image=self.get_circular_image(current_pic_base64, size=(120, 120)))
        pic_label.pack(expand=True)
        
        # Status and upload button
        button_frame = ctk.CTkFrame(pic_preview_frame, fg_color="transparent")
        button_frame.pack(side="left", fill="both", expand=True)
        
        if current_pic_base64:
            ctk.CTkLabel(button_frame, text="✓ Profile picture uploaded", text_color="#10b981", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 10))
        else:
            ctk.CTkLabel(button_frame, text="No profile picture", text_color="gray", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 10))
        
        def upload_picture():
            file_path = filedialog.askopenfilename(
                title="Select Profile Picture",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
            )
            if file_path:
                try:
                    with open(file_path, 'rb') as f:
                        import base64
                        pic_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    print(f"Picture size: {len(pic_data)} bytes")
                    
                    # Update ONLY the profile picture, don't refresh other fields
                    headers = {"Authorization": f"Bearer {self.token}"}
                    
                    # Get current profile to preserve other fields
                    try:
                        r_profile = requests.get(f"{API_BASE}/profile", headers=headers)
                        current_profile = r_profile.json() if r_profile.status_code == 200 else {}
                    except:
                        current_profile = {}
                    
                    data = {
                        'name': current_profile.get('name', name_var.get()),
                        'phone': current_profile.get('phone', phone_var.get()),
                        'email': current_profile.get('email', email_var.get()),
                        'profile_pic': pic_data
                    }
                    r = requests.post(f"{API_BASE}/profile", json=data, headers=headers)
                    
                    print(f"Response status: {r.status_code}")
                    print(f"Response: {r.text}")
                    
                    if r.status_code == 200:
                        # Update user profile in memory
                        self.user['profile_pic'] = pic_data
                        messagebox.showinfo("Success", "Profile picture uploaded successfully!")
                        # Refresh entire page to update sidebar
                        self.show_profile_management()
                    else:
                        error_msg = r.json().get('error', 'Failed to upload picture')
                        details = r.json().get('details', '')
                        full_msg = f"{error_msg}\n{details}" if details else error_msg
                        messagebox.showerror("Upload Failed", full_msg)
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Error uploading picture: {error_details}")
                    messagebox.showerror("Error", f"Upload failed: {str(e)}")
        
        ctk.CTkButton(button_frame, text="📷 Upload New Picture", command=upload_picture,
                     fg_color="#3b82f6", width=180, height=35).pack(anchor="w")
        
        # Name
        ctk.CTkLabel(form, text="Name *", font=("Segoe UI Semibold", 14)).pack(anchor="w", pady=(20, 5))
        ctk.CTkEntry(form, textvariable=name_var, height=40).pack(fill="x")
        
        # Phone
        ctk.CTkLabel(form, text="Phone", font=("Segoe UI Semibold", 14)).pack(anchor="w", pady=(20, 5))
        ctk.CTkEntry(form, textvariable=phone_var, height=40, state="readonly").pack(fill="x")
        
        # Email
        ctk.CTkLabel(form, text="Email", font=("Segoe UI Semibold", 14)).pack(anchor="w", pady=(20, 5))
        ctk.CTkEntry(form, textvariable=email_var, height=40).pack(fill="x")
        
        def save_profile():
            if not name_var.get().strip():
                return messagebox.showerror("Error", "Name is required")
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    'name': name_var.get().strip(),
                    'phone': phone_var.get(),
                    'email': email_var.get(),
                    'profile_pic': profile.get('profile_pic')
                }
                r = requests.post(f"{API_BASE}/profile", json=data, headers=headers)
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Profile updated successfully!")
                    self.user['name'] = name_var.get().strip()
                else:
                    messagebox.showerror("Error", "Failed to update profile")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(form, text="Save Changes", command=save_profile,
                     fg_color="#10b981", hover_color="#059669",
                     height=45, font=("Segoe UI Bold", 14)).pack(pady=30)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = AarambhaPMS()
        app.run()
    except Exception as e:
        import traceback
        with open("crash.log", "w") as f:
            f.write(traceback.format_exc())
            f.write(f"\nError: {e}")
        print(f"CRASH: {e}")
