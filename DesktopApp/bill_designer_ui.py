
import customtkinter as ctk
from tkinter import Canvas, StringVar, IntVar, BooleanVar, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
import requests
import json
import base64

class BillDesignerUI:
    def __init__(self, main_app):
        self.app = main_app
        self.root = main_app.root
        self.api_base = getattr(self.app, 'API_BASE', "http://127.0.0.1:5000/api")
        
        # --- Bill State ---
        self.paper_size = StringVar(value="A4") # A4, A5
        self.orientation = StringVar(value="PORTRAIT")
        
        self.config = {
            "header": {
                "show_logo": True,
                "title": "TAX INVOICE",
                "font_size": 20,
                "align": "center" # left, center, right
            },
            "columns": { # Visibility
                "sn": True,
                "batch": True,
                "expiry": True,
                "qty": True,
                "rate": True,
                "discount": False,
                "amount": True
            },
            "total": {
                "subtotal": True,
                "vat": True,
                "discount": True,
                "words": True
            },
            "footer": {
                "terms": "Goods once sold cannot be returned.",
                "thank_you": "Thank you for your visit!",
                "show_user": True,
                "show_datetime": True
            }
        }
        
        # Image Buffers (bytes)
        self.stamp_bytes = None
        self.signature_bytes = None
        
        # Canvas Scaling
        self.scale = 0.75 # Preview scale - increased for better visibility
        self.a4_dim = (595, 842) # Points (approx 1/72 inch)
        self.a5_dim = (420, 595)
        
    def show(self, container):
        # Layout: Left Control Panel (Scrollable), Right Preview (Canvas)
        
        # 1. Main Grid
        self.main_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # 2. Control Panel
        self.controls = ctk.CTkScrollableFrame(self.main_frame, width=350, fg_color=("#ffffff", "#1e293b"))
        self.controls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.init_controls()

        # 3. Preview Panel
        self.preview_frame = ctk.CTkFrame(self.main_frame, fg_color="#cbd5e1") # Light gray background for contrast
        self.preview_frame.grid(row=0, column=1, sticky="nsew")
        
        self.canvas = Canvas(self.preview_frame, bg="white", highlightthickness=0)
        self.canvas.pack(expand=True, padx=20, pady=20)
        
        # Load Existing Data
        self.load_design()
        
    def init_controls(self):
        # A. Page Setup
        ctk.CTkLabel(self.controls, text="📄 Page Setup", font=("Segoe UI Bold", 16)).pack(anchor="w", pady=(10, 5))
        
        page_frame = ctk.CTkFrame(self.controls, fg_color="transparent")
        page_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(page_frame, text="Size:").grid(row=0, column=0, padx=5)
        ctk.CTkOptionMenu(page_frame, variable=self.paper_size, values=["A4", "A5"], width=80, command=self.update_preview).grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(page_frame, text="Orient:").grid(row=0, column=2, padx=5)
        ctk.CTkOptionMenu(page_frame, variable=self.orientation, values=["PORTRAIT", "LANDSCAPE"], width=100, command=self.update_preview).grid(row=0, column=3, padx=5)
        
        # B. Header
        ctk.CTkLabel(self.controls, text="🏗️ Header", font=("Segoe UI Bold", 16)).pack(anchor="w", pady=(15, 5))
        
        self.fv_title = StringVar(value=self.config['header']['title'])
        ctk.CTkEntry(self.controls, textvariable=self.fv_title, placeholder_text="Bill Title").pack(fill="x", pady=5)
        self.fv_title.trace_add("write", lambda *args: self.update_preview())
        
        h_opts = ctk.CTkFrame(self.controls, fg_color="transparent")
        h_opts.pack(fill="x")
        self.fv_logo = BooleanVar(value=self.config['header']['show_logo'])
        ctk.CTkCheckBox(h_opts, text="Show Logo", variable=self.fv_logo, command=self.update_preview).pack(side="left")
        
        # Manual PAN/ODA
        ctk.CTkLabel(self.controls, text="Information:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(5, 0))
        self.fv_pan = StringVar(value=self.config['header'].get('pan', self.app.user.get('pan_number', '')))
        ctk.CTkEntry(self.controls, textvariable=self.fv_pan, placeholder_text="PAN Number").pack(fill="x", pady=2)
        self.fv_pan.trace_add("write", lambda *args: self.update_preview())
        
        self.fv_oda = StringVar(value=self.config['header'].get('oda', self.app.user.get('oda_number', '')))
        ctk.CTkEntry(self.controls, textvariable=self.fv_oda, placeholder_text="DDA/ODA Number").pack(fill="x", pady=2)
        self.fv_oda.trace_add("write", lambda *args: self.update_preview())
        
        # C. Columns (Body)
        ctk.CTkLabel(self.controls, text="📝 Columns", font=("Segoe UI Bold", 16)).pack(anchor="w", pady=(15, 5))
        
        col_frame = ctk.CTkFrame(self.controls, fg_color="transparent")
        col_frame.pack(fill="x")
        
        self.col_vars = {}
        for i, (key, label) in enumerate([("batch", "Batch No"), ("expiry", "Expiry"), ("discount", "Discount")]):
            var = BooleanVar(value=self.config['columns'][key])
            ctk.CTkCheckBox(col_frame, text=label, variable=var, command=self.update_preview).grid(row=i, column=0, sticky="w", pady=2)
            self.col_vars[key] = var
            
        # D. Footer & Images
        ctk.CTkLabel(self.controls, text="🦶 Footer", font=("Segoe UI Bold", 16)).pack(anchor="w", pady=(15, 5))
        
        self.fv_terms = StringVar(value=self.config['footer']['terms'])
        ctk.CTkEntry(self.controls, textvariable=self.fv_terms, placeholder_text="Terms").pack(fill="x", pady=5)
        self.fv_terms.trace_add("write", lambda *args: self.update_preview())
        
        # Uploads
        btn_frame = ctk.CTkFrame(self.controls, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Upload Stamp", command=lambda: self.upload_image('stamp'), width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Upload Sig", command=lambda: self.upload_image('signature'), width=140).pack(side="right", padx=5)
        
        # Save
        ctk.CTkButton(self.controls, text="💾 SAVE DESIGN", command=self.save_design, fg_color="#10b981", height=40).pack(fill="x", pady=30)
        
    def upload_image(self, type_):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if path:
            with open(path, "rb") as f:
                data = f.read()
            if type_ == 'stamp':
                self.stamp_bytes = data
            else:
                self.signature_bytes = data
            self.update_preview()

    def load_design(self):
        try:
            headers = {"Authorization": f"Bearer {self.app.token}"}
            r = requests.get(f"{self.api_base}/bill-design", headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data.get('found'):
                    d = data['design']
                    self.paper_size.set(d['paper_size'])
                    self.orientation.set(d['orientation'])
                    if d['config']:
                        self.config.update(d['config']) # Merge defaults
                        self.update_ui_vars()
                    
                    if d.get('stamp_base64'):
                        self.stamp_bytes = base64.b64decode(d['stamp_base64'])
                    if d.get('signature_base64'):
                        self.signature_bytes = base64.b64decode(d['signature_base64'])
            
            self.update_preview()
        except Exception as e:
            print(f"Load Error: {e}")

    def update_ui_vars(self):
        # Sync simple vars back to UI
        self.fv_title.set(self.config['header']['title'])
        self.fv_logo.set(self.config['header']['show_logo'])
        self.fv_pan.set(self.config['header'].get('pan', ''))
        self.fv_oda.set(self.config['header'].get('oda', ''))
        self.fv_terms.set(self.config['footer']['terms'])
        for k, v in self.col_vars.items():
            v.set(self.config['columns'][k])

    def save_design(self):
        # Update config object from UI
        self.config['header']['title'] = self.fv_title.get()
        self.config['header']['show_logo'] = self.fv_logo.get()
        self.config['header']['pan'] = self.fv_pan.get()
        self.config['header']['oda'] = self.fv_oda.get()
        self.config['footer']['terms'] = self.fv_terms.get()
        for k, v in self.col_vars.items():
            self.config['columns'][k] = v.get()
            
        # Prepare Payload
        try:
            files = {}
            if self.stamp_bytes:
                files['stamp_image'] = ('stamp.png', self.stamp_bytes, 'image/png')
            if self.signature_bytes:
                files['signature_image'] = ('sig.png', self.signature_bytes, 'image/png')
                
            data = {
                'paper_size': self.paper_size.get(),
                'orientation': self.orientation.get(),
                'config': json.dumps(self.config)
            }
            
            headers = {"Authorization": f"Bearer {self.app.token}"}
            # Remove content-type for multipart (requests handles it)
            
            r = requests.post(f"{self.api_base}/bill-design", headers=headers, data=data, files=files)
            
            if r.status_code == 200:
                messagebox.showinfo("Success", "Bill Design Saved Successfully!")
            else:
                messagebox.showerror("Error", f"Failed: {r.text}")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_preview(self, *args):
        # DRAW CANVAS
        self.canvas.delete("all")
        
        # Dimensions
        w, h = self.a4_dim if self.paper_size.get() == "A4" else self.a5_dim
        if self.orientation.get() == "LANDSCAPE":
            w, h = h, w
        
        # Apply Screen Scale
        sw = int(w * self.scale)
        sh = int(h * self.scale)
        
        self.canvas.config(width=sw, height=sh)
        self.canvas.create_rectangle(0, 0, sw, sh, fill="white", outline="gray")
        
        # --- DRAW CONTENT (SIMULATED) ---
        ctx = ImageDraw.Draw(Image.new("RGB", (1,1))) # Just for font metrics if needed
        
        # Header
        y_off = 20 * self.scale
        if self.fv_logo.get():
            self.canvas.create_rectangle(20*self.scale, y_off, 70*self.scale, y_off+50*self.scale, fill="#ddd", outline="#aaa")
            self.canvas.create_text(45*self.scale, y_off+25*self.scale, text="LOGO")
            y_off += 60 * self.scale
            
        # Hospital Name (Mock)
        self.canvas.create_text(sw/2, y_off, text=self.app.user.get('pharmacy_name', 'Pharmacy Name'), font=("Arial", int(16*self.scale), "bold"), fill="black")
        y_off += 25 * self.scale
        self.canvas.create_text(sw/2, y_off, text=self.app.user.get('address', 'Address, City'), font=("Arial", int(10*self.scale)), fill="gray")
        y_off += 20 * self.scale
        
        # PAN / ODA
        pan = self.fv_pan.get() or self.app.user.get('pan_number', '-')
        oda = self.fv_oda.get() or self.app.user.get('oda_number', '-')
        info_text = f"PAN No: {pan}  |  DDA No: {oda}"
        self.canvas.create_text(sw/2, y_off, text=info_text, font=("Arial", int(9*self.scale)), fill="black")
        y_off += 25 * self.scale
        
        # Title
        self.canvas.create_text(sw/2, y_off, text=self.fv_title.get().upper(), font=("Arial", int(14*self.scale), "bold"), fill="black")
        y_off += 30 * self.scale
        
        # --- BILL METADATA (Invoice No, Customer, etc.) ---
        mx = 20 * self.scale
        ty = y_off
        start_y_meta = ty

        if self.config['header'].get('align', 'center') == 'left': # Default to 'center' if not set
            # Invoice Info (Left)
            self.canvas.create_text(mx, ty, text="Invoice No: INV-XXXX", anchor="w", font=("Arial", int(9*self.scale)))
            ty += 12 * self.scale
            self.canvas.create_text(mx, ty, text="Date: YYYY-MM-DD", anchor="w", font=("Arial", int(9*self.scale)))
            ty += 12 * self.scale
            
            # Show Sold By if enabled or default
            user_name = self.app.user.get('name', 'Admin') if hasattr(self.app, 'user') else 'Admin'
            self.canvas.create_text(mx, ty, text=f"Sold By: {user_name}", anchor="w", font=("Arial", int(9*self.scale)))
            ty += 12 * self.scale
            
            self.canvas.create_text(mx, ty, text="Payment Mode: CASH", anchor="w", font=("Arial", int(9*self.scale)))
            
            # Customer (Right)
            cx = sw - mx
            cy = start_y_meta
            self.canvas.create_text(cx, cy, text="Customer: Walk-in", anchor="e", font=("Arial", int(9*self.scale)))
        else:
            # Centered/Split Logic (Default)
            self.canvas.create_text(mx, ty, text="Invoice No: INV-XXXX", anchor="w", font=("Arial", int(9*self.scale)))
            ty += 12 * self.scale
            self.canvas.create_text(mx, ty, text="Date: YYYY-MM-DD", anchor="w", font=("Arial", int(9*self.scale)))
            ty += 12 * self.scale
            
            user_name = self.app.user.get('name', 'Admin') if hasattr(self.app, 'user') else 'Admin'
            self.canvas.create_text(mx, ty, text=f"Sold By: {user_name}", anchor="w", font=("Arial", int(9*self.scale)))
            ty += 12 * self.scale
            
            self.canvas.create_text(mx, ty, text="Payment Mode: CASH", anchor="w", font=("Arial", int(9*self.scale)))
            
            self.canvas.create_text(sw-mx, start_y_meta, text="Customer: Walk-in", anchor="e", font=("Arial", int(9*self.scale)))
        ty += 20 * self.scale
        
        y_off = ty
        
        # Table Header
        headers = ["SN", "Particulars"]
        if self.col_vars['batch'].get(): headers.append("Batch")
        if self.col_vars['expiry'].get(): headers.append("Exp")
        headers.extend(["Qty", "Rate"])
        if self.col_vars['discount'].get(): headers.append("Dis%")
        headers.append("Amount")
        
        col_w = sw / len(headers)
        for i, txt in enumerate(headers):
            x = i * col_w
            self.canvas.create_rectangle(x, y_off, x+col_w, y_off+25*self.scale, fill="#eee", outline="#ccc")
            self.canvas.create_text(x+col_w/2, y_off+12.5*self.scale, text=txt, font=("Arial", int(9*self.scale), "bold"))
            
        y_off += 25 * self.scale
        # Mock Rows
        if self.orientation.get() == "LANDSCAPE" and self.paper_size.get() == "A5":
            rows = 4
        elif self.paper_size.get() == "A5":
            rows = 8
        else:
            rows = 15
            
        for r in range(rows):
            for i in range(len(headers)):
                x = i * col_w
                self.canvas.create_rectangle(x, y_off, x+col_w, y_off+20*self.scale, outline="#eee")
            y_off += 20 * self.scale
            
        # Total Section (Bottom Right)
        ty = y_off + 10 * self.scale
        
        # Subtotal
        self.canvas.create_text(sw-100*self.scale, ty, text="Subtotal: Rs. 1500.00", anchor="e", font=("Arial", int(9*self.scale)))
        ty += 15 * self.scale
        
        # Discount (Mock)
        self.canvas.create_text(sw-100*self.scale, ty, text="Discount: Rs. 0.00", anchor="e", font=("Arial", int(9*self.scale)))
        ty += 20 * self.scale
        
        # Grand Total
        self.canvas.create_text(sw-100*self.scale, ty, text="Total: Rs. 1500.00", anchor="e", font=("Arial", int(11*self.scale), "bold"))
        
        # Footer
        fy = sh - (60 * self.scale)
        self.canvas.create_line(10*self.scale, fy, sw-10*self.scale, fy, fill="#ccc")
        fy += 15 * self.scale
        self.canvas.create_text(sw/2, fy, text=self.fv_terms.get(), font=("Arial", int(8*self.scale)), fill="gray")
        
        # Images (Stamp/Sig)
        if self.stamp_bytes:
            # Resize for preview
            img = Image.open(io.BytesIO(self.stamp_bytes))
            img.thumbnail((80, 80))
            self._tk_stamp = ImageTk.PhotoImage(img) # Keep ref
            self.canvas.create_image(sw - 100*self.scale, sh - 150*self.scale, image=self._tk_stamp, anchor="nw")
            
        if self.signature_bytes:
             img = Image.open(io.BytesIO(self.signature_bytes))
             img.thumbnail((100, 50))
             self._tk_sig = ImageTk.PhotoImage(img)
             self.canvas.create_image(sw - 100*self.scale, sh - 100*self.scale, image=self._tk_sig, anchor="nw")

