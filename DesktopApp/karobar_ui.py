import customtkinter as ctk
from tkinter import messagebox, StringVar, Toplevel, filedialog
import requests
from datetime import datetime
from date_utils import DateUtils
import pandas as pd
import os

API_BASE = "http://127.0.0.1:5000/api"

class KarobarUI:
    def __init__(self, main_app):
        self.app = main_app
        self.root = main_app.root

    def show_karobar_main(self):
        """Main Karobar Screen - List Accounts & Quick Actions"""
        for widget in self.root.winfo_children():
            widget.destroy()

        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)

        token = self.app.token
        user = self.app.user
        
        if not user:
            messagebox.showerror("Error", "User not logged in")
            return

        nav_items = self.app.get_super_admin_nav() if user['role'] == 'SUPER_ADMIN' else self.app.get_admin_nav()
        self.app.create_sidebar(main_container, nav_items, "Karobar")

        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="🏦 Karobar (Sahakari/Ledger)", font=("Segoe UI Black", 28)).pack(side="left")
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        if self.app.user['role'] in ['ADMIN', 'SUPER_ADMIN']:
            ctk.CTkButton(btn_frame, text="⚙️ Manage Accounts", command=self.show_accounts_management,
                         fg_color="#3b82f6", height=40).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="🏷️ Categories", command=self.show_categories_management,
                         fg_color="#6366f1", height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="📜 Statement", command=self.show_statement_ledger,
                     fg_color="#f59e0b", height=40).pack(side="left", padx=5)

        # Action Cards
        actions_frame = ctk.CTkFrame(content, fg_color="transparent")
        actions_frame.pack(fill="x", pady=20)
        
        self.create_action_card(actions_frame, "💰 CASH IN", "Deposit/Saving", "#10b981", self.open_cash_in_dialog).pack(side="left", padx=10, expand=True, fill="both")
        self.create_action_card(actions_frame, "💸 CASH OUT", "Withdraw/Expense", "#ef4444", self.open_cash_out_dialog).pack(side="left", padx=10, expand=True, fill="both")

        # Accounts Overview
        ctk.CTkLabel(content, text="Account Balances", font=("Segoe UI Bold", 18)).pack(anchor="w", pady=(20, 10))
        self.accounts_list_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.accounts_list_frame.pack(fill="x")
        
        self.load_accounts_overview()

    def create_action_card(self, parent, title, subtitle, color, command):
        card = ctk.CTkFrame(parent, height=150, fg_color=("#ffffff", "#1e293b"), corner_radius=15, cursor="hand2")
        card.pack_propagate(False)
        
        lbl_title = ctk.CTkLabel(card, text=title, font=("Segoe UI Black", 24), text_color=color)
        lbl_title.pack(pady=(30, 5))
        
        ctk.CTkLabel(card, text=subtitle, font=("Segoe UI", 14), text_color="gray").pack()
        
        card.bind("<Button-1>", lambda e: command())
        lbl_title.bind("<Button-1>", lambda e: command())
        
        return card

    def load_accounts_overview(self):
        for w in self.accounts_list_frame.winfo_children(): w.destroy()
        
        try:
            r = requests.get(f"{API_BASE}/karobar/accounts", headers={"Authorization": f"Bearer {self.app.token}"})
            if r.status_code == 200:
                accounts = r.json()
                for acc in accounts:
                    row = ctk.CTkFrame(self.accounts_list_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
                    row.pack(fill="x", pady=5)
                    
                    ctk.CTkLabel(row, text=acc['bank_name'], font=("Segoe UI Bold", 14), width=200, anchor="w").pack(side="left", padx=15, pady=15)
                    ctk.CTkLabel(row, text=acc['account_number'], width=150).pack(side="left", padx=10)
                    ctk.CTkLabel(row, text=f"Rs. {acc['current_balance']:,}", font=("Segoe UI Bold", 16), text_color="#10b981").pack(side="right", padx=20)
            else:
                ctk.CTkLabel(self.accounts_list_frame, text="Failed to load accounts").pack()
        except Exception as e:
            print(f"Error: {e}")

    # --- DIALOGS (CASH IN / OUT) ---

    def open_cash_in_dialog(self): self.open_transaction_dialog("IN")
    def open_cash_out_dialog(self): self.open_transaction_dialog("OUT")

    def open_transaction_dialog(self, type):
        dialog = Toplevel(self.root)
        dialog.title(f"New Transaction - {'Cash In' if type == 'IN' else 'Cash Out'}")
        dialog.geometry("500x700")
        dialog.configure(bg="#0f172a")
        dialog.grab_set()

        # UI elements here... (Account dropdown, Category dropdown, Amount, Date, Reason)
        # For brevity, implementing save logic
        
        # Load data for dropdowns
        try:
            acc_r = requests.get(f"{API_BASE}/karobar/accounts", headers={"Authorization": f"Bearer {self.app.token}"})
            cat_r = requests.get(f"{API_BASE}/karobar/categories", headers={"Authorization": f"Bearer {self.app.token}"})
            accounts = acc_r.json() if acc_r.status_code == 200 else []
            categories = cat_r.json() if cat_r.status_code == 200 else []
        except:
            accounts, categories = [], []

        ctk.CTkLabel(dialog, text=f"{'Deposit' if type == 'IN' else 'Withdrawal'}", font=("Segoe UI Black", 24), text_color="#10b981" if type == 'IN' else "#ef4444").pack(pady=20)
        
        # Account Selection
        ctk.CTkLabel(dialog, text="Select Account").pack(anchor="w", padx=40)
        acc_names = [f"{a['bank_name']} ({a['account_number']})" for a in accounts]
        acc_var = StringVar(value=acc_names[0] if acc_names else "No Accounts")
        acc_dropdown = ctk.CTkComboBox(dialog, values=acc_names, variable=acc_var, width=400)
        acc_dropdown.pack(pady=(0, 15))

        # Category Selection
        ctk.CTkLabel(dialog, text="Category").pack(anchor="w", padx=40)
        cat_names = [c['name'] for c in categories if c['type'] in [type, 'BOTH']]
        cat_var = StringVar(value=cat_names[0] if cat_names else "Misc")
        cat_dropdown = ctk.CTkComboBox(dialog, values=cat_names, variable=cat_var, width=400)
        cat_dropdown.pack(pady=(0, 15))

        # Amount
        ctk.CTkLabel(dialog, text="Amount").pack(anchor="w", padx=40)
        amt_entry = ctk.CTkEntry(dialog, placeholder_text="0.00", width=400)
        amt_entry.pack(pady=(0, 15))

        # Reason (for Out) / Reference (for In)
        ctk.CTkLabel(dialog, text="Reason / Reference").pack(anchor="w", padx=40)
        ref_entry = ctk.CTkEntry(dialog, placeholder_text="Details...", width=400)
        ref_entry.pack(pady=(0, 15))

        def save():
            amt = amt_entry.get()
            if not amt or float(amt) <= 0: return messagebox.showerror("Error", "Invalid amount")
            
            selected_acc = accounts[acc_names.index(acc_var.get())]
            selected_cat = next(c for c in categories if c['name'] == cat_var.get())

            payload = {
                "account_id": selected_acc['id'],
                "category_id": selected_cat['id'],
                "type": type,
                "amount": float(amt),
                "reason": ref_entry.get() if type == 'OUT' else "",
                "reference_no": ref_entry.get() if type == 'IN' else "",
                "notes": ""
            }

            try:
                r = requests.post(f"{API_BASE}/karobar/transaction", json=payload, headers={"Authorization": f"Bearer {self.app.token}"})
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Transaction recorded!")
                    dialog.destroy()
                    self.show_karobar_main()
                else:
                    messagebox.showerror("Error", r.json().get('error', 'Failed'))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(dialog, text="Submit Transaction", command=save, fg_color="#10b981" if type == 'IN' else "#ef4444", height=45).pack(pady=30)

    # --- STATEMENT LEDGER ---

    def show_statement_ledger(self):
        """Statement Ledger screen with filters"""
        for widget in self.root.winfo_children(): widget.destroy()
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        nav_items = self.app.get_super_admin_nav() if self.app.user['role'] == 'SUPER_ADMIN' else self.app.get_admin_nav()
        self.app.create_sidebar(main_container, nav_items, "Karobar")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(content, text="📜 Karobar Statement", font=("Segoe UI Black", 28)).pack(anchor="w", pady=(0, 20))
        
        # Filter Bar
        filter_frame = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 20))
        
        # ... (Filters implementation omitted for brevity, adding a simple load button)
        ctk.CTkButton(filter_frame, text="📥 Export Excel", command=self.export_excel, fg_color="#10b981").pack(side="right", padx=10, pady=10)

        self.statement_list_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.statement_list_frame.pack(fill="both", expand=True)
        self.load_statements()

    def load_statements(self):
        for w in self.statement_list_frame.winfo_children(): w.destroy()
        try:
            r = requests.get(f"{API_BASE}/karobar/statements", headers={"Authorization": f"Bearer {self.app.token}"})
            if r.status_code == 200:
                data = r.json()
                # Table Header
                h = ctk.CTkFrame(self.statement_list_frame, fg_color=("#e2e8f0", "#334155"))
                h.pack(fill="x", pady=5)
                ctk.CTkLabel(h, text="Date", width=150).pack(side="left", padx=5)
                ctk.CTkLabel(h, text="Type", width=80).pack(side="left", padx=5)
                ctk.CTkLabel(h, text="Account", width=150).pack(side="left", padx=5)
                ctk.CTkLabel(h, text="Amount", width=100).pack(side="left", padx=5)
                ctk.CTkLabel(h, text="Balance", width=100).pack(side="left", padx=5)
                ctk.CTkLabel(h, text="By", width=100).pack(side="right", padx=5)

                for s in data:
                    row = ctk.CTkFrame(self.statement_list_frame, fg_color=("#ffffff", "#1e293b"))
                    row.pack(fill="x", pady=2)
                    ad_date_str = s['created_at'].split('T')[0]
                    bs_date = DateUtils.ad_to_bs(ad_date_str)
                    ctk.CTkLabel(row, text=bs_date, width=150).pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=s['type'], width=80, text_color="#10b981" if s['type']=='IN' else "#ef4444").pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=s['bank_name'], width=150, anchor="w").pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=f"{s['amount']:,}", width=100).pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=f"{s['balance_after']:,}", width=100, font=("Segoe UI Bold", 12)).pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=s['performed_by_name'], width=100).pack(side="right", padx=5)
        except Exception as e:
            print(f"Error: {e}")

    def export_excel(self):
        try:
            r = requests.get(f"{API_BASE}/karobar/statements", headers={"Authorization": f"Bearer {self.app.token}"})
            if r.status_code == 200:
                df = pd.DataFrame(r.json())
                # Convert Date to BS
                if 'created_at' in df.columns:
                    df['created_at'] = df['created_at'].apply(lambda x: DateUtils.ad_to_bs(x.split('T')[0]) if x else '')
                    df.rename(columns={'created_at': 'Date (BS)'}, inplace=True)
                path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
                if path:
                    df.to_excel(path, index=False)
                    messagebox.showinfo("Success", "Excel exported!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- ACCOUNTS MANAGEMENT (ADMIN) ---

    def show_accounts_management(self):
        """Full account management screen"""
        for widget in self.root.winfo_children(): widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.app.get_super_admin_nav() if self.app.user['role'] == 'SUPER_ADMIN' else self.app.get_admin_nav()
        self.app.create_sidebar(main_container, nav_items, "Karobar")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="🏦 Sahakari / Bank Accounts", font=("Segoe UI Black", 28)).pack(side="left")
        ctk.CTkButton(header, text="+ Add New Account", command=self.open_account_dialog,
                     fg_color="#10b981", height=40).pack(side="right")

        self.acc_list_container = ctk.CTkFrame(content, fg_color="transparent")
        self.acc_list_container.pack(fill="both", expand=True)
        self.load_accounts_list()

    def load_accounts_list(self):
        for w in self.acc_list_container.winfo_children(): w.destroy()
        try:
            r = requests.get(f"{API_BASE}/karobar/accounts", headers={"Authorization": f"Bearer {self.app.token}"})
            if r.status_code == 200:
                accounts = r.json()
                for acc in accounts:
                    row = ctk.CTkFrame(self.acc_list_container, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
                    row.pack(fill="x", pady=5)
                    
                    info = ctk.CTkFrame(row, fg_color="transparent")
                    info.pack(side="left", padx=20, pady=15)
                    
                    ctk.CTkLabel(info, text=acc['bank_name'], font=("Segoe UI Bold", 16)).pack(anchor="w")
                    ctk.CTkLabel(info, text=f"{acc['account_name']} | {acc['account_number']}", text_color="gray").pack(anchor="w")
                    
                    details = ctk.CTkFrame(row, fg_color="transparent")
                    details.pack(side="right", padx=20)
                    
                    ctk.CTkLabel(details, text=f"Bal: Rs. {acc['current_balance']:,}", font=("Segoe UI Bold", 18), text_color="#10b981").pack(side="left", padx=20)
                    ctk.CTkButton(details, text="Edit", width=60, command=lambda a=acc: self.open_account_dialog(a)).pack(side="left", padx=5)
        except Exception as e: print(f"Error: {e}")

    def open_account_dialog(self, account=None):
        dialog = Toplevel(self.root)
        dialog.title("Edit Account" if account else "Add New Account")
        dialog.geometry("600x800")
        dialog.configure(bg="#0f172a")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Sahakari/Bank Details", font=("Segoe UI Black", 20)).pack(pady=20)
        
        fields = [
            ("Bank Name", "bank_name"),
            ("Address", "address"),
            ("Account Name", "account_name"),
            ("Account Number", "account_number"),
            ("Holder Name", "holder_name"),
            ("Contact", "contact"),
            ("Opening Balance", "opening_balance"),
            ("Opening Date (YYYY-MM-DD)", "opening_balance_date")
        ]
        
        entries = {}
        for label, key in fields:
            ctk.CTkLabel(dialog, text=label).pack(anchor="w", padx=50)
            e = ctk.CTkEntry(dialog, width=500)
            if account: e.insert(0, account.get(key, ""))
            e.pack(pady=(0, 10))
            entries[key] = e

        def save():
            data = {k: v.get() for k, v in entries.items()}
            try:
                if account:
                    r = requests.put(f"{API_BASE}/karobar/accounts/{account['id']}", json=data, headers={"Authorization": f"Bearer {self.app.token}"})
                else:
                    r = requests.post(f"{API_BASE}/karobar/accounts", json=data, headers={"Authorization": f"Bearer {self.app.token}"})
                
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Account saved!")
                    dialog.destroy()
                    self.show_accounts_management()
                else:
                    messagebox.showerror("Error", r.json().get('error', 'Failed'))
            except Exception as e: messagebox.showerror("Error", str(e))

        ctk.CTkButton(dialog, text="Save Account", command=save, fg_color="#10b981", height=45).pack(pady=30)

    # --- CATEGORIES MANAGEMENT ---

    def show_categories_management(self):
        """Full category management screen"""
        for widget in self.root.winfo_children(): widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        nav_items = self.app.get_super_admin_nav() if self.app.user['role'] == 'SUPER_ADMIN' else self.app.get_admin_nav()
        self.app.create_sidebar(main_container, nav_items, "Karobar")
        
        content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="🏷️ Saving Categories", font=("Segoe UI Black", 28)).pack(side="left")
        
        # Add quick form
        form = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
        form.pack(fill="x", pady=10)
        
        name_entry = ctk.CTkEntry(form, placeholder_text="New Category Name", width=300)
        name_entry.pack(side="left", padx=10, pady=10)
        
        type_var = StringVar(value="BOTH")
        ctk.CTkOptionMenu(form, values=["IN", "OUT", "BOTH"], variable=type_var).pack(side="left", padx=10)
        
        def add_cat():
            name = name_entry.get()
            if not name: return
            try:
                r = requests.post(f"{API_BASE}/karobar/categories", json={"name": name, "type": type_var.get()}, headers={"Authorization": f"Bearer {self.app.token}"})
                if r.status_code == 200:
                    name_entry.delete(0, 'end')
                    self.show_categories_management()
                else: messagebox.showerror("Error", "Failed to add")
            except Exception as e: print(e)

        ctk.CTkButton(form, text="Add Category", command=add_cat, fg_color="#6366f1").pack(side="right", padx=10)

        self.cat_list_container = ctk.CTkFrame(content, fg_color="transparent")
        self.cat_list_container.pack(fill="both", expand=True, pady=20)
        self.load_categories_list()

    def load_categories_list(self):
        for w in self.cat_list_container.winfo_children(): w.destroy()
        try:
            r = requests.get(f"{API_BASE}/karobar/categories", headers={"Authorization": f"Bearer {self.app.token}"})
            if r.status_code == 200:
                for cat in r.json():
                    row = ctk.CTkFrame(self.cat_list_container, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
                    row.pack(fill="x", pady=2)
                    ctk.CTkLabel(row, text=cat['name'], width=200, anchor="w").pack(side="left", padx=15, pady=8)
                    ctk.CTkLabel(row, text=cat['type'], width=100, text_color="gray").pack(side="left", padx=15)
        except Exception as e: print(e)
