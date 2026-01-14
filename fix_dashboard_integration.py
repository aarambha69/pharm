
# Integrate DashboardUI into main.py
import re

file_path = 'DesktopApp/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add Import
if "from dashboard_ui import DashboardUI" not in "".join(lines[:20]):
    lines.insert(1, "from dashboard_ui import DashboardUI\n")
    print("Added import")

# 2. Add API_BASE in __init__
init_found = False
for i, line in enumerate(lines):
    if "self.root = self" in line and not init_found:
        if "self.API_BASE =" not in lines[i+1]:
            lines.insert(i+1, "        self.API_BASE = API_BASE\n")
            print("Added self.API_BASE")
        init_found = True
        break

# 3. Replace show_super_admin_dashboard
# We will construct the new method code
new_method = """    def show_super_admin_dashboard(self):
        \"\"\"Complete Super Admin Dashboard\"\"\"
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        self.create_sidebar(main_container, self.get_super_admin_nav(), "Dashboard")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True)
        
        dashboard = DashboardUI(self)
        dashboard.show(content)

    def show_admin_dashboard(self):
        \"\"\"Admin Dashboard\"\"\"
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        self.create_sidebar(main_container, self.get_admin_nav(), "Dashboard")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True)
        
        dashboard = DashboardUI(self)
        dashboard.show(content)

"""

# Find the existing function
start = -1
end = -1
for i, line in enumerate(lines):
    if "def show_super_admin_dashboard(self):" in line:
        start = i
        # Find where it ends (next def)
        for j in range(i+1, len(lines)):
            if lines[j].strip().startswith("def "):
                end = j
                break
        break

if start != -1:
    print(f"Replacing function at lines {start}-{end}")
    # Remove old function
    del lines[start:end]
    # Insert new methods
    lines.insert(start, new_method)
else:
    print("Could not find show_super_admin_dashboard")

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("✅ main.py updated")
