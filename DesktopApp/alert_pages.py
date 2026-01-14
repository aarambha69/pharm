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
            else:
                messagebox.showerror("Error", "Failed to load alerts")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def display_alerts(items):
        # Clear existing
        for w in alert_list.winfo_children():
            w.destroy()
        
        if not items:
            ctk.CTkLabel(alert_list, text="✅ No low stock items", 
                       font=("Segoe UI", 16), text_color="gray").pack(pady=50)
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
        
        # Table rows
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
                         command=lambda i=item: show_details(i),
                         fg_color="#3b82f6").pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="📱 SMS", width=60, height=30,
                         command=lambda i=item: send_sms(i),
                         fg_color="#10b981").pack(side="left", padx=2)
    
    def show_details(item):
        exp_date = item.get('expiry_date', 'N/A')
        if exp_date and 'T' in exp_date: 
            exp_date_ad = exp_date.split('T')[0]
            exp_date = f"{DateUtils.ad_to_bs(exp_date_ad)} (BS)"
        
        messagebox.showinfo("Product Details", 
                          f"Medicine: {item['medicine_name']}\n"
                          f"Vendor: {item.get('vendor_name', 'N/A')}\n"
                          f"Batch: {item.get('batch_number', 'N/A')}\n"
                          f"Expiry: {exp_date}\n"
                          f"Current Stock: {item['quantity']}\n"
                          f"Low Stock Threshold: {item.get('threshold', 10)}")
    
    def send_sms(item):
        try:
            phone = self.user.get('phone', '')
            if not phone:
                messagebox.showerror("Error", "Admin phone not found")
                return
            
            productData = {
                'id': item.get('medicine_id'),
                'name': item.get('medicine_name'),
                'vendor': item.get('vendor_name', 'N/A'),
                'batch': item.get('batch_number', ''),
                'stock': item.get('quantity', 0),
                'unit': 'units'
            }
            
            payload = {'type': 'LOW_STOCK', 'productData': productData, 'toNumber': phone}
            headers = {"Authorization": f"Bearer {self.token}"}
            r = requests.post(f"{API_BASE}/sms/send-alert", json=payload, headers=headers)
            
            if r.status_code == 200:
                messagebox.showinfo("Success", "SMS sent successfully!")
            elif r.status_code == 429:
                messagebox.showwarning("Already Sent", "SMS already sent recently")
            else:
                messagebox.showerror("Error", f"Failed: {r.text}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # Alert list container
    alert_list = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
    alert_list.pack(fill="both", expand=True, pady=(0, 20))
    
    # Refresh button
    ctk.CTkButton(content, text="🔄 Refresh", command=load_alerts, 
                 fg_color="#3b82f6", height=40).pack(pady=10)
    
    # Load data
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
            else:
                messagebox.showerror("Error", "Failed to load alerts")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def display_alerts(items):
        # Clear existing
        for w in alert_list.winfo_children():
            w.destroy()
        
        if not items:
            ctk.CTkLabel(alert_list, text="✅ No expiring items", 
                       font=("Segoe UI", 16), text_color="gray").pack(pady=50)
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
        
        # Table rows
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
                         command=lambda i=item: show_details(i),
                         fg_color="#3b82f6").pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="📱 SMS", width=60, height=30,
                         command=lambda i=item: send_sms(i),
                         fg_color="#10b981").pack(side="left", padx=2)
    
    def show_details(item):
        messagebox.showinfo("Product Details", 
                          f"Medicine: {item['medicine_name']}\n"
                          f"Vendor: {item.get('vendor_name', 'N/A')}\n"
                          f"Batch: {item.get('batch_number', 'N/A')}\n"
                          f"Expiry: {item.get('expiry_date', '').split('T')[0]}\n"
                          f"Current Stock: {item.get('quantity', 0)}")
    
    def send_sms(item):
        try:
            phone = self.user.get('phone', '')
            if not phone:
                messagebox.showerror("Error", "Admin phone not found")
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
            
            payload = {'type': 'EXPIRY', 'productData': productData, 'toNumber': phone}
            headers = {"Authorization": f"Bearer {self.token}"}
            r = requests.post(f"{API_BASE}/sms/send-alert", json=payload, headers=headers)
            
            if r.status_code == 200:
                messagebox.showinfo("Success", "SMS sent successfully!")
            elif r.status_code == 429:
                messagebox.showwarning("Already Sent", "SMS already sent recently")
            else:
                messagebox.showerror("Error", f"Failed: {r.text}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # Alert list container
    alert_list = ctk.CTkFrame(content, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
    alert_list.pack(fill="both", expand=True, pady=(0, 20))
    
    # Refresh button
    ctk.CTkButton(content, text="🔄 Refresh", command=load_alerts, 
                 fg_color="#3b82f6", height=40).pack(pady=10)
    
    # Load data
    load_alerts()

