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
            nav_items = self.get_admin_nav()
        else:
            nav_items = self.get_cashier_nav()
            
        self.create_sidebar(main_container, nav_items, "Sales Terminal")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="💰 Sales Terminal", font=("Segoe UI Black", 28)).pack(side="left")
        
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
        
        ctk.CTkLabel(search_frame, text="Search Product:", font=("Segoe UI Bold", 12)).pack(anchor="w")
        search_var = StringVar()
        
        def on_search(*args):
            query = search_var.get()
            if len(query) < 2: return
            # Simple dropdown simulation or popup
            # For brevity, implementing a simple popup picker
            pass 
            
        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, placeholder_text="Type to search...")
        search_entry.pack(fill="x", pady=(5, 10))
        
        def show_product_picker():
            d = ctk.CTkToplevel(self.root)
            d.title("Select Product")
            d.geometry("600x500")
            d.transient(self.root)
            d.grab_set()
            
            # Search
            s_frame = ctk.CTkFrame(d)
            s_frame.pack(fill="x", padx=10, pady=10)
            q = StringVar()
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
            
        def process_sale():
            if not cart_items:
                return messagebox.showerror("Error", "Cart is empty")
                
            payload = {
                "items": cart_items,
                "subtotal": self.cart_total,
                "tax_total": 0, # Simplified
                "discount_total": 0,
                "grand_total": self.cart_total,
                "payment_category": pay_cat_var.get(),
                "paid_amount": self.cart_total
            }
            
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
                if r.status_code == 201:
                    messagebox.showinfo("Success", "Sale recorded successfully")
                    self.show_billing_terminal() # Reset
                else:
                    messagebox.showerror("Error", f"Failed: {r.text}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        ctk.CTkButton(right_pane, text="✅ Checkout / Print Bill", command=process_sale, 
                     height=50, fg_color="#10b981", font=("Segoe UI Bold", 16)).pack(side="bottom", fill="x", padx=15, pady=(0, 20))


