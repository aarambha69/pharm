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
        grn_no = f"GRN-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        grn_entry = ctk.CTkEntry(grn_col, height=40, font=("Consolas", 13))
        grn_entry.insert(0, grn_no)
        grn_entry.configure(state="readonly", text_color="#6366f1")
        grn_entry.pack(fill="x", pady=2)
        
        # Purchase Date
        date_col = ctk.CTkFrame(row1, fg_color="transparent")
        date_col.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(date_col, text="Purchase Date *", font=("Segoe UI Bold", 11), text_color="gray").pack(anchor="w")
        date_var = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
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
            ("S.N", 40), ("Product", 200), ("Batch", 100), ("Expiry", 90),
            ("P.Rate", 80), ("MRP", 80), ("Qty", 60), ("Free", 50),
            ("Disc%", 60), ("VAT", 50), ("Total", 100), ("", 40)
        ]
        
        for label, width in cols:
            ctk.CTkLabel(headers_frame, text=label, width=width, font=("Segoe UI Bold", 11), text_color="gray").pack(side="left", padx=2)
        
        # Scrollable items container
        items_scroll = ctk.CTkScrollableFrame(grid_inner, fg_color="transparent", height=300)
        items_scroll.pack(fill="both", expand=True)
        
        self.grn_rows = []
        
        def add_grn_row():
            idx = len(self.grn_rows) + 1
            row_f = ctk.CTkFrame(items_scroll, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            
            # S.N
            ctk.CTkLabel(row_f, text=str(idx), width=40, font=("Segoe UI", 11)).pack(side="left", padx=2)
            
            # Product
            p_id = IntVar(value=0)
            p_name = StringVar()
            p_ent = ctk.CTkEntry(row_f, textvariable=p_name, width=200, placeholder_text="Search Product...")
            p_ent.pack(side="left", padx=2)
            
            # Batch
            batch = StringVar()
            ctk.CTkEntry(row_f, textvariable=batch, width=100, placeholder_text="Batch No").pack(side="left", padx=2)
            
            # Expiry
            exp = StringVar()
            ctk.CTkEntry(row_f, textvariable=exp, width=90, placeholder_text="YYYY-MM").pack(side="left", padx=2)
            
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
                'p_id': p_id, 'p_name': p_name, 'batch': batch, 'exp': exp,
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
                "purchase_date": date_var.get(),
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
                    "expiry_date": r['exp'].get(),
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
