
# Restore show_super_admin_dashboard
import re

file_path = 'DesktopApp/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# The original function code
original_func = """    def show_super_admin_dashboard(self):
        \"\"\"Complete Super Admin Dashboard\"\"\"
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

"""

# Find range to replace
start = -1
end = -1
for i, line in enumerate(lines):
    if "def show_super_admin_dashboard(self):" in line:
        start = i
    if "def show_admin_dashboard(self):" in line:
        end = i # End before the next function starts
        break

if start != -1 and end != -1:
    print(f"Replacing lines {start}-{end}")
    del lines[start:end]
    lines.insert(start, original_func)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ show_super_admin_dashboard restored")
else:
    print("Could not locate functions")
