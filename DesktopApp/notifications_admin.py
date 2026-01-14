def show_notification_management(self):
    """Notification Management for Admin - Create and manage internal notifications"""
    for widget in self.root.winfo_children():
        widget.destroy()
    
    main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
    main_container.pack(fill="both", expand=True)
    
    nav_items = self.get_super_admin_nav() if self.user['role'] == 'SUPER_ADMIN' else self.get_admin_nav()
    self.create_sidebar(main_container, nav_items, "Notifications")
    
    content = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
    content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
    
    # Header
    header = ctk.CTkFrame(content, fg_color="transparent")
    header.pack(fill="x", pady=(0, 20))
    
    ctk.CTkLabel(header, text="📢 Notification Management", font=("Segoe UI Black", 28)).pack(side="left")
    ctk.CTkButton(header, text="+ Create Notification", command=self.show_create_notification_dialog,
                 fg_color="#10b981", height=40).pack(side="right")
    
    # Filter tabs
    filter_frame = ctk.CTkFrame(content, fg_color="transparent")
    filter_frame.pack(fill="x", pady=(0, 20))
    
    status_var = StringVar(value="active")
    
    def load_notifications():
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            params = {'status': status_var.get()}
            r = requests.get(f"{API_BASE}/notifications/admin", headers=headers, params=params)
            if r.status_code == 200:
                display_notifications(r.json())
        except Exception as e:
            print(f"Error: {e}")
    
    for stat in [("Active", "active"), ("Expired", "expired"), ("Upcoming", "upcoming"), ("All", "")]:
        btn = ctk.CTkButton(filter_frame, text=stat[0], width=100,
                           command=lambda s=stat[1]: [status_var.set(s), load_notifications()],
                           fg_color="#3b82f6" if stat[1] == "active" else "#6b7280")
        btn.pack(side="left", padx=5)
    
    def display_notifications(notifs):
        for w in notif_list.winfo_children():
            w.destroy()
        
        if not notifs:
            ctk.CTkLabel(notif_list, text="No notifications", text_color="gray").pack(pady=50)
            return
        
        for notif in notifs:
            card = ctk.CTkFrame(notif_list, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
            card.pack(fill="x", pady=10, padx=5)
            
            # Priority color
            priority_colors = {'normal': '#3b82f6', 'important': '#f59e0b', 'urgent': '#ef4444'}
            color = priority_colors.get(notif.get('priority', 'normal'), '#3b82f6')
            
            left_bar = ctk.CTkFrame(card, fg_color=color, width=5)
            left_bar.pack(side="left", fill="y")
            
            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)
            
            # Title and priority
            title_row = ctk.CTkFrame(content_frame, fg_color="transparent")
            title_row.pack(fill="x")
            
            ctk.CTkLabel(title_row, text=notif['title'], font=("Segoe UI Bold", 16)).pack(side="left")
            ctk.CTkLabel(title_row, text=notif.get('priority', 'normal').upper(),
                        font=("Segoe UI Bold", 10), text_color=color).pack(side="left", padx=10)
            
            # Description preview
            desc_preview = notif['description'][:100] + ("..." if len(notif['description']) > 100 else "")
            ctk.CTkLabel(content_frame, text=desc_preview, font=("Segoe UI", 12),
                       text_color="gray").pack(anchor="w", pady=(5, 0))
            
            # Date range and read status
            info_row = ctk.CTkFrame(content_frame, fg_color="transparent")
            info_row.pack(fill="x", pady=(10, 0))
            
            dates = f"{notif['start_date']} → {notif['end_date']}"
            ctk.CTkLabel(info_row, text=dates, font=("Segoe UI", 11),
                       text_color="gray").pack(side="left")
            
            read_info = f"{notif.get('read_count', 0)}/{notif.get('total_recipients', 0)} read"
            ctk.CTkLabel(info_row, text=read_info, font=("Segoe UI", 11),
                       text_color="#10b981").pack(side="left", padx=20)
    
    notif_list = ctk.CTkFrame(content, fg_color="transparent")
    notif_list.pack(fill="both", expand=True)
    
    load_notifications()

def show_create_notification_dialog(self):
    """Create notification dialog"""
    dialog = ctk.CTkToplevel(self.root)
    dialog.title("Create Notification")
    dialog.geometry("600x700")
    dialog.grab_set()
    dialog.transient(self.root)
    
    # Center
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
    y = (dialog.winfo_screenheight() // 2) - (700 // 2)
    dialog.geometry(f"600x700+{x}+{y}")
    
    ctk.CTkLabel(dialog, text="Create Notification", font=("Segoe UI Bold", 20)).pack(pady=20)
    
    form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
    form.pack(fill="both", expand=True, padx=30)
    
    # Form fields
    title_var = StringVar()
    desc_var = StringVar()
    priority_var = StringVar(value="normal")
    target_var = StringVar(value="all")
    start_var = StringVar()
    end_var = StringVar()
    
    ctk.CTkLabel(form, text="Title *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
    ctk.CTkEntry(form, textvariable=title_var, height=35).pack(fill="x")
    
    ctk.CTkLabel(form, text="Description *", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
    desc_textbox = ctk.CTkTextbox(form, height=120)
    desc_textbox.pack(fill="x")
    
    ctk.CTkLabel(form, text="Priority", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
    ctk.CTkOptionMenu(form, variable=priority_var, values=["normal", "important", "urgent"]).pack(fill="x")
    
    ctk.CTkLabel(form, text="Target", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
    ctk.CTkOptionMenu(form, variable=target_var, values=["all", "selected"]).pack(fill="x")
    
    ctk.CTkLabel(form, text="Start Date * (YYYY-MM-DD)", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
    ctk.CTkEntry(form, textvariable=start_var, placeholder_text="2026-01-15", height=35).pack(fill="x")
    
    ctk.CTkLabel(form, text="End Date * (YYYY-MM-DD)", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(10, 5))
    ctk.CTkEntry(form, textvariable=end_var, placeholder_text="2026-01-20", height=35).pack(fill="x")
    
    def create_notification():
        title = title_var.get().strip()
        description = desc_textbox.get("1.0", "end-1c").strip()
        
        if not title or not description or not start_var.get() or not end_var.get():
            return messagebox.showerror("Error", "All required fields must be filled", parent=dialog)
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            data = {
                'title': title,
                'description': description,
                'priority': priority_var.get(),
                'target': target_var.get(),
                'start_date': start_var.get(),
                'end_date': end_var.get(),
                'cashier_ids': []  # For 'all' target
            }
            
            r = requests.post(f"{API_BASE}/notifications", json=data, headers=headers)
            if r.status_code == 200:
                messagebox.showinfo("Success", "Notification created!", parent=dialog)
                dialog.destroy()
                self.show_notification_management()
            else:
                messagebox.showerror("Error", r.json().get('message', 'Failed'), parent=dialog)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=dialog)
    
    btn_frame = ctk.CTkFrame(form, fg_color="transparent")
    btn_frame.pack(pady=20)
    
    ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                 fg_color="#6b7280", width=100, height=40).pack(side="left", padx=5)
    ctk.CTkButton(btn_frame, text="Create", command=create_notification,
                 fg_color="#10b981", width=150, height=40).pack(side="left", padx=5)

