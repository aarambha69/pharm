
import customtkinter as ctk
from tkinter import StringVar, IntVar
import requests
import threading
import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class DashboardUI:
    def __init__(self, main_app):
        self.app = main_app
        self.root = main_app.root
        self.api_base = "http://localhost:5000/api" # Hardcoded or passed? passing logic better
        if hasattr(self.app, 'api_base'):
            self.api_base = self.app.api_base # Future proofing if main.py changes definition

    def show(self, container):
        # 1. Main Scrollable Container
        self.scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # 2. Header & Controls
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header, text="📊 Dashboard", font=("Segoe UI Black", 28)).pack(side="left")
        
        # Date Filter (Visual only for v1 MVP, backend defaults to 'Today'/'Last 30')
        self.date_filter = StringVar(value="Today")
        ctk.CTkOptionMenu(header, variable=self.date_filter, values=["Today", "Yesterday", "Last 7 Days", "This Month"], width=120).pack(side="right", padx=10)
        
        ctk.CTkButton(header, text="🔄 Refresh", width=100, command=self.load_data, fg_color="#3b82f6").pack(side="right")

        # 3. KPI Grid
        self.kpi_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=(0, 20))
        self.kpi_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.kpi_widgets = {}
        self.create_kpi_card("Sales Today", "Rs. 0", "🛒 0 Bills", "#10b981", 0)
        self.create_kpi_card("Profit Est.", "Rs. 0", "📈 Today", "#3b82f6", 1)
        self.create_kpi_card("Purchases", "Rs. 0", "📦 0 GRN", "#f59e0b", 2)
        self.create_kpi_card("Stock Warning", "0 Items", "⚠️ Low/Exp", "#ef4444", 3)

        # 4. Charts Section
        chart_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        chart_row.pack(fill="x", pady=(0, 20))
        chart_row.grid_columnconfigure((0, 1), weight=1)

        self.chart_l = ctk.CTkFrame(chart_row, fg_color=("#ffffff", "#1e293b"), corner_radius=15, height=300)
        self.chart_l.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chart_l.pack_propagate(False)
        ctk.CTkLabel(self.chart_l, text="Sales Trend (Last 30 Days)", font=("Segoe UI Bold", 14)).pack(pady=10)

        self.chart_r = ctk.CTkFrame(chart_row, fg_color=("#ffffff", "#1e293b"), corner_radius=15, height=300)
        self.chart_r.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.chart_r.pack_propagate(False)
        ctk.CTkLabel(self.chart_r, text="Payment Mix (Today)", font=("Segoe UI Bold", 14)).pack(pady=10)

        # 5. Alerts Section
        alert_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        alert_row.pack(fill="x", pady=(0, 20))
        alert_row.grid_columnconfigure((0, 1), weight=1)

        # Expiry
        self.exp_frame = ctk.CTkFrame(alert_row, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        self.exp_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(self.exp_frame, text="⚠️ Near Expiry (Top 10)", font=("Segoe UI Bold", 14), text_color="#ef4444").pack(pady=10, anchor="w", padx=15)
        self.exp_list = ctk.CTkFrame(self.exp_frame, fg_color="transparent")
        self.exp_list.pack(fill="both", expand=True, padx=10, pady=5)

        # Low Stock
        self.low_frame = ctk.CTkFrame(alert_row, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        self.low_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(self.low_frame, text="📉 Low Stock (Top 10)", font=("Segoe UI Bold", 14), text_color="#f59e0b").pack(pady=10, anchor="w", padx=15)
        self.low_list = ctk.CTkFrame(self.low_frame, fg_color="transparent")
        self.low_list.pack(fill="both", expand=True, padx=10, pady=5)

        # 5.5 Cashier Collections (New)
        coll_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        coll_row.pack(fill="x", pady=(0, 20))
        
        self.coll_frame = ctk.CTkFrame(coll_row, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        self.coll_frame.pack(fill="x")
        
        ctk.CTkLabel(self.coll_frame, text="💰 Cashier Collections (Today)", font=("Segoe UI Bold", 14), text_color="#10b981").pack(pady=10, anchor="w", padx=15)
        
        self.cashier_list = ctk.CTkFrame(self.coll_frame, fg_color="transparent")
        self.cashier_list.pack(fill="both", expand=True, padx=10, pady=5)

        # 6. Quick Actions
        qa_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        qa_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(qa_frame, text="⚡ Quick Actions", font=("Segoe UI Bold", 18)).pack(anchor="w", pady=(0, 10))
        
        qa_grid = ctk.CTkFrame(qa_frame, fg_color="transparent")
        qa_grid.pack(fill="x")
        
        actions = [
            ("New Bill", "💰", getattr(self.app, 'show_billing_terminal', None)),
            ("Add Stock", "📦", getattr(self.app, 'show_add_stock_dialog', None)),
            ("Payment Methods", "💳", getattr(self.app, 'show_payment_methods', None)),
            ("Reports", "📄", None) # Placeholder
        ]
        
        for i, (txt, icon, cmd) in enumerate(actions):
            if cmd:
                btn = ctk.CTkButton(qa_grid, text=f"{icon} {txt}", command=cmd, height=40, 
                                  fg_color=("#3b82f6", "#1e40af"), font=("Segoe UI Semibold", 13))
                btn.grid(row=0, column=i, padx=5, sticky="ew")
        
        qa_grid.grid_columnconfigure((0,1,2,3), weight=1)

        # Footer
        ctk.CTkLabel(self.scroll, text="Aarambha Softwares - Pharmacy Management System v2.0", text_color="gray", font=("Segoe UI", 10)).pack(pady=20)

        # Load Data
        self.load_data()

    def create_kpi_card(self, title, value_placeholder, sub_placeholder, color, col_idx):
        card = ctk.CTkFrame(self.kpi_frame, fg_color=color, corner_radius=15, height=120)
        card.grid(row=0, column=col_idx, padx=10, sticky="ew")
        card.pack_propagate(False)
        
        ctk.CTkLabel(card, text=title, text_color="white", font=("Segoe UI", 14)).pack(anchor="w", padx=15, pady=(15, 0))
        val_lbl = ctk.CTkLabel(card, text=value_placeholder, text_color="white", font=("Segoe UI Black", 24))
        val_lbl.pack(anchor="w", padx=15, pady=(5, 0))
        sub_lbl = ctk.CTkLabel(card, text=sub_placeholder, text_color="white", font=("Segoe UI", 12))
        sub_lbl.pack(anchor="w", padx=15, pady=(5, 0))
        
        self.kpi_widgets[title] = (val_lbl, sub_lbl)

    def load_data(self):
        # Run in thread
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            token = self.app.token
            headers = {"Authorization": f"Bearer {token}"}
            
            # 1. KPIs
            r_kpi = requests.get(f"{self.app.API_BASE}/dashboard/kpi", headers=headers) 
            if r_kpi.status_code == 200:
                self.app.root.after(0, self.update_kpis, r_kpi.json())
                
            # 2. Alerts
            r_alerts = requests.get(f"{self.app.API_BASE}/dashboard/alerts", headers=headers)
            if r_alerts.status_code == 200:
                self.app.root.after(0, self.update_alerts, r_alerts.json())
                
            # 3. Charts
            r_charts = requests.get(f"{self.app.API_BASE}/dashboard/charts", headers=headers)
            if r_charts.status_code == 200:
                self.app.root.after(0, self.update_charts, r_charts.json())

            # 4. Cashier Stats (New)
            r_cashier = requests.get(f"{self.app.API_BASE}/reports/cashier-collections", headers=headers)
            if r_cashier.status_code == 200:
                 self.app.root.after(0, self.update_cashier_stats, r_cashier.json())
                
        except Exception as e:
            print(f"Dashboard Error: {e}")

    def update_cashier_stats(self, data):
        # Clear existing
        for w in self.cashier_list.winfo_children(): w.destroy()
        
        if not data:
            ctk.CTkLabel(self.cashier_list, text="No collection data available", text_color="gray").pack(pady=10)
            return

        # Header Row
        h_frame = ctk.CTkFrame(self.cashier_list, fg_color="transparent")
        h_frame.pack(fill="x", pady=2)
        cols = [("Cashier Name", 150), ("Total Bills", 80), ("Cash Collect", 100), ("Digital Collect", 100), ("Total", 100)]
        for txt, w in cols:
            ctk.CTkLabel(h_frame, text=txt, font=("Segoe UI Bold", 12), width=w, anchor="w").pack(side="left", padx=5)

        # Data Rows
        for row in data:
            r_frame = ctk.CTkFrame(self.cashier_list, fg_color=("white", "#334155"))
            r_frame.pack(fill="x", pady=2)
            
            vals = [
                row.get('cashier_name', 'Unknown'),
                str(row.get('total_bills', 0)),
                f"Rs. {float(row.get('cash_collection', 0)):,.2f}",
                f"Rs. {float(row.get('digital_collection', 0)):,.2f}",
                f"Rs. {float(row.get('total_collection', 0)):,.2f}"
            ]
            
            for val, (col_name, w) in zip(vals, cols):
                # Highlight Total
                font = ("Segoe UI Bold", 12) if col_name == "Total" else ("Segoe UI", 12)
                color = "#10b981" if col_name == "Total" else ("#ef4444" if col_name == "Total Bills" else None) # Just styling example
                
                ctk.CTkLabel(r_frame, text=val, font=font, width=w, anchor="w", text_color=color).pack(side="left", padx=5)

    def update_kpis(self, data):
        # Sales
        s = data.get('sales', {})
        self.kpi_widgets["Sales Today"][0].configure(text=f"Rs. {s.get('total_amount', 0):,.0f}")
        self.kpi_widgets["Sales Today"][1].configure(text=f"🛒 {s.get('count', 0)} Bills")
        
        # Profit
        p = data.get('profit', 0)
        self.kpi_widgets["Profit Est."][0].configure(text=f"Rs. {float(p):,.0f}")
        
        # Purchase
        pu = data.get('purchases', {})
        self.kpi_widgets["Purchases"][0].configure(text=f"Rs. {pu.get('total_amount', 0):,.0f}")
        self.kpi_widgets["Purchases"][1].configure(text=f"📦 {pu.get('count', 0)} GRN")
        
        # Stock
        st = data.get('stock', {})
        self.kpi_widgets["Stock Warning"][0].configure(text=f"{st.get('low_stock', 0)} Low Stock")
        self.kpi_widgets["Stock Warning"][1].configure(text=f"⚠️ {st.get('expiring', 0)} Expiring")

    def update_alerts(self, data):
        # Clear existing
        for w in self.exp_list.winfo_children(): w.destroy()
        for w in self.low_list.winfo_children(): w.destroy()
        
        # Expiry
        ex = data.get('expiry', [])
        if not ex:
            ctk.CTkLabel(self.exp_list, text="No immediate expiry alerts", text_color="gray").pack()
        for item in ex:
            row = ctk.CTkFrame(self.exp_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{item['medicine_name']} ({item['batch_number']})", anchor="w", width=100).pack(side="left")
            date_lbl = ctk.CTkLabel(row, text=item['expiry_date'].split('T')[0], text_color="#ef4444", width=70)
            date_lbl.pack(side="left", padx=5)
            # Details Button
            details_btn = ctk.CTkButton(row, text="📋", width=30, height=24,
                                       command=lambda i=item: self.show_product_details(i),
                                       fg_color="#3b82f6", hover_color="#2563eb")
            details_btn.pack(side="right", padx=2)
            # SMS Button
            sms_btn = ctk.CTkButton(row, text="📱", width=30, height=24, 
                                   command=lambda i=item: self.send_expiry_sms(i),
                                   fg_color="#10b981", hover_color="#059669")
            sms_btn.pack(side="right", padx=2)
            
        # Low Stock
        ls = data.get('lowStock', [])
        if not ls:
             ctk.CTkLabel(self.low_list, text="Stock levels healthy", text_color="gray").pack()
        for item in ls:
            row = ctk.CTkFrame(self.low_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=item['medicine_name'], anchor="w", width=100).pack(side="left")
            qty_lbl = ctk.CTkLabel(row, text=f"Qty: {item['quantity']}", text_color="#f59e0b", width=70)
            qty_lbl.pack(side="left", padx=5)
            # Details Button
            details_btn = ctk.CTkButton(row, text="📋", width=30, height=24,
                                       command=lambda i=item: self.show_product_details(i),
                                       fg_color="#3b82f6", hover_color="#2563eb")
            details_btn.pack(side="right", padx=2)
            # SMS Button
            sms_btn = ctk.CTkButton(row, text="📱", width=30, height=24,
                                   command=lambda i=item: self.send_lowstock_sms(i),
                                   fg_color="#10b981", hover_color="#059669")
            sms_btn.pack(side="right", padx=2)
    
    def show_product_details(self, item):
        """Display detailed product information in a popup"""
        from tkinter import Toplevel
        
        detail_window = Toplevel(self.root)
        detail_window.title("Product Details")
        detail_window.geometry("500x600")
        detail_window.configure(bg="#1e293b")
        
        # Main container
        container = ctk.CTkScrollableFrame(detail_window, fg_color="#1e293b")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(container, text="📦 Product Information", 
                    font=("Segoe UI Black", 20)).pack(pady=(0, 20))
        
        # Product details
        details = [
            ("Medicine Name", item.get('medicine_name', 'N/A')),
            ("Batch Number", item.get('batch_number', 'N/A')),
            ("Quantity", str(item.get('quantity', 0))),
            ("Expiry Date", item.get('expiry_date', 'N/A').split('T')[0] if item.get('expiry_date') else 'N/A'),
            ("Threshold", str(item.get('threshold', 'N/A'))),
        ]
        
        for label, value in details:
            row_frame = ctk.CTkFrame(container, fg_color="#334155", corner_radius=10)
            row_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row_frame, text=label, 
                        font=("Segoe UI Semibold", 13),
                        anchor="w").pack(side="left", padx=15, pady=10)
            
            ctk.CTkLabel(row_frame, text=value,
                        font=("Segoe UI", 13),
                        anchor="e").pack(side="right", padx=15, pady=10)
        
        # Fetch additional details from API
        try:
            medicine_id = item.get('medicine_id') or item.get('id')
            if medicine_id:
                headers = {"Authorization": f"Bearer {self.app.token}"}
                r = requests.get(f"{self.app.API_BASE}/medicines/{medicine_id}", headers=headers)
                if r.status_code == 200:
                    med_data = r.json()
                    
                    ctk.CTkLabel(container, text="Additional Information",
                                font=("Segoe UI Bold", 16)).pack(pady=(20, 10))
                    
                    additional = [
                        ("Generic Name", med_data.get('generic_name', 'N/A')),
                        ("Brand Name", med_data.get('brand_name', 'N/A')),
                        ("Category", med_data.get('category', 'N/A')),
                        ("Manufacturer", med_data.get('manufacturer', 'N/A')),
                        ("Strength", med_data.get('strength', 'N/A')),
                        ("Dosage Form", med_data.get('dosage_form', 'N/A')),
                    ]
                    
                    for label, value in additional:
                        if value and value != 'N/A':
                            row_frame = ctk.CTkFrame(container, fg_color="#334155", corner_radius=10)
                            row_frame.pack(fill="x", pady=5)
                            
                            ctk.CTkLabel(row_frame, text=label,
                                        font=("Segoe UI Semibold", 13),
                                        anchor="w").pack(side="left", padx=15, pady=10)
                            
                            ctk.CTkLabel(row_frame, text=value,
                                        font=("Segoe UI", 13),
                                        anchor="e").pack(side="right", padx=15, pady=10)
        except Exception as e:
            print(f"Error fetching medicine details: {e}")
        
        # Close button
        ctk.CTkButton(container, text="Close", 
                     command=detail_window.destroy,
                     fg_color="#ef4444", hover_color="#dc2626",
                     height=40).pack(pady=20)
    
    def send_expiry_sms(self, item):
        try:
            from tkinter import messagebox
            phone = self.app.user.get('phone', '')
            if not phone:
                messagebox.showerror("Error", "Admin phone number not found")
                return
            
            productData = {
                'id': item.get('medicine_id'),
                'name': item.get('medicine_name'),
                'vendor': item.get('vendor_name', 'N/A'),
                'expiry': item.get('expiry_date', '').split('T')[0],
                'batch': item.get('batch_number', ''),
                'stock': item.get('quantity', 0),
                'unit': 'units'
            }
            
            payload = {
                'type': 'EXPIRY',
                'productData': productData,
                'toNumber': phone
            }
            
            headers = {"Authorization": f"Bearer {self.app.token}"}
            r = requests.post(f"{self.app.API_BASE}/sms/send-alert", json=payload, headers=headers)
            
            if r.status_code == 200:
                messagebox.showinfo("Success", "SMS sent successfully!")
            elif r.status_code == 429:
                messagebox.showwarning("Already Sent", "SMS already sent for this item recently")
            else:
                messagebox.showerror("Error", f"Failed to send SMS: {r.text}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))
    
    def send_lowstock_sms(self, item):
        try:
            from tkinter import messagebox
            phone = self.app.user.get('phone', '')
            if not phone:
                messagebox.showerror("Error", "Admin phone number not found")
                return
            
            productData = {
                'id': item.get('medicine_id'),
                'name': item.get('medicine_name'),
                'vendor': item.get('vendor_name', 'N/A '),
                'batch': item.get('batch_number', ''),
                'stock': item.get('quantity', 0),
                'unit': 'units'
            }
            
            payload = {
                'type': 'LOW_STOCK',
                'productData': productData,
                'toNumber': phone
            }
            
            headers = {"Authorization": f"Bearer {self.app.token}"}
            r = requests.post(f"{self.app.API_BASE}/sms/send-alert", json=payload, headers=headers)
            
            if r.status_code == 200:
                messagebox.showinfo("Success", "SMS sent successfully!")
            elif r.status_code == 429:
                messagebox.showwarning("Already Sent", "SMS already sent for this item recently")
            else:
                messagebox.showerror("Error", f"Failed to send SMS: {r.text}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))

    def update_charts(self, data):
        # Sales Trend
        trend = data.get('trend', [])
        dates = [d['date'].split('T')[0][5:] for d in trend] # MM-DD
        amounts = [float(d['amount']) for d in trend]
        
        fig1 = Figure(figsize=(5, 3), dpi=80, facecolor="#1e293b") # Matches dark theme card bg
        ax1 = fig1.add_subplot(111)
        ax1.set_facecolor("#1e293b")
        ax1.plot(dates, amounts, marker='o', color='#3b82f6', linewidth=2)
        ax1.tick_params(colors='white', labelsize=8)
        # Hide borders
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_color('white')
        ax1.spines['left'].set_color('white')
        
        # Clean current widget if any (simple approach: clear frame children except label)
        for w in self.chart_l.winfo_children():
            if not isinstance(w, ctk.CTkLabel): w.destroy()
            
        canvas1 = FigureCanvasTkAgg(fig1, master=self.chart_l)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Payment Mix
        mix = data.get('mix', [])
        labels = [m['payment_category'] for m in mix]
        sizes = [float(m['amount']) for m in mix]
        
        if sizes:
            fig2 = Figure(figsize=(5, 3), dpi=80, facecolor="#1e293b")
            ax2 = fig2.add_subplot(111)
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
                   textprops={'color':"white", 'fontsize': 8}, colors=['#10b981', '#3b82f6', '#f59e0b'])
            
            for w in self.chart_r.winfo_children():
                if not isinstance(w, ctk.CTkLabel): w.destroy()
                
            canvas2 = FigureCanvasTkAgg(fig2, master=self.chart_r)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        else:
             ctk.CTkLabel(self.chart_r, text="No Sales Today", text_color="gray").pack(pady=50)
