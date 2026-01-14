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
        """Add Payment Method Dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Payment Method")
        dialog.geometry("500x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Scrollable form
        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Name
        ctk.CTkLabel(form, text="Name *", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        name_var = StringVar()
        ctk.CTkEntry(form, textvariable=name_var, placeholder_text="e.g., eSewa, Khalti", height=40).pack(fill="x", pady=(0, 15))
        
        # Category
        ctk.CTkLabel(form, text="Category *", font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 5))
        category_var = StringVar(value="DIGITAL")
        ctk.CTkOptionMenu(form, variable=category_var, values=["CASH", "DIGITAL"], height=40).pack(fill="x", pady=(0, 15))
        
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
        notes_text = ctk.CTkTextbox(form, height=80)
        notes_text.pack(fill="x", pady=(0, 15))
        
        # Show on Billing
        show_billing_var = BooleanVar(value=True)
        ctk.CTkCheckBox(form, text="Show on Billing Terminal", variable=show_billing_var,
                       font=("Segoe UI Bold", 12)).pack(anchor="w", pady=(0, 15))
        
        def save():
            if not name_var.get().strip():
                return messagebox.showerror("Error", "Name is required")
            
            payload = {
                "name": name_var.get().strip(),
                "category": category_var.get(),
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
        """Upload QR Code Dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Upload QR - {method['name']}")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form, text=f"QR Code for {method['name']}", font=("Segoe UI Black", 18)).pack(pady=(0, 20))
        
        # Preview
        preview_label = ctk.CTkLabel(form, text="No QR uploaded yet", width=300, height=300,
                                     fg_color=("#e2e8f0", "#334155"), corner_radius=10)
        preview_label.pack(pady=20)
        
        selected_file = {"path": None}
        
        def select_file():
            from tkinter import filedialog
            filepath = filedialog.askopenfilename(
                title="Select QR Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg")]
            )
            if filepath:
                # Validate size
                size = os.path.getsize(filepath)
                if size > 2 * 1024 * 1024:
                    return messagebox.showerror("Error", "File size must be less than 2MB")
                
                selected_file['path'] = filepath
                
                # Show preview
                try:
                    img = Image.open(filepath)
                    img.thumbnail((300, 300))
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(300, 300))
                    preview_label.configure(image=photo, text="")
                    preview_label.image = photo
                except:
                    messagebox.showerror("Error", "Failed to load image")
        
        ctk.CTkButton(form, text="📁 Select QR Image (PNG/JPG)", command=select_file,
                     height=50, fg_color="#6366f1").pack(pady=10)
        
        def upload():
            if not selected_file['path']:
                return messagebox.showerror("Error", "Please select an image")
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                with open(selected_file['path'], 'rb') as f:
                    files = {'qr_image': f}
                    resp = requests.post(f"{API_BASE}/payment-methods/{method['id']}/upload-qr",
                                        files=files, headers=headers)
                if resp.status_code == 200:
                    messagebox.showinfo("Success", "QR uploaded successfully")
                    dialog.destroy()
                    self.show_payment_methods()
                else:
                    messagebox.showerror("Error", resp.json().get('error', 'Upload failed'))
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(form, text="✅ Upload QR Code", command=upload, height=50,
                     fg_color="#10b981", font=("Segoe UI Bold", 14)).pack(pady=20)
