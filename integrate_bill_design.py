
# Integrate Bill Design into main.py
import re

file_path = 'DesktopApp/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add Import
if "from bill_designer_ui import BillDesignerUI" not in "".join(lines[:25]):
    lines.insert(2, "from bill_designer_ui import BillDesignerUI\n")
    print("Added Import")

# 2. Add show_bill_designer method
method_code = """    def show_bill_designer(self):
        \"\"\"Bill Designer (Admin Only)\"\"\"
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = ctk.CTkFrame(self.root, fg_color=("#f1f5f9", "#0f172a"))
        main_container.pack(fill="both", expand=True)
        
        self.create_sidebar(main_container, self.get_admin_nav(), "Bill Design")
        
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        self.add_back_button(header)
        ctk.CTkLabel(header, text="🎨 Bill Designer", font=("Segoe UI Black", 24)).pack(side="left", padx=20)
        
        designer = BillDesignerUI(self)
        designer.show(content)

"""

# Insert before run() method or at end of class
insert_idx = -1
for i, line in enumerate(lines):
    if "def run(self):" in line:
        insert_idx = i
        break
        
if insert_idx != -1:
    lines.insert(insert_idx, method_code)
    print("Added Method")

# 3. Add to get_admin_nav
# We look for the 'mapping' list in 'get_admin_nav'
found_map = False
for i, line in enumerate(lines):
    if "('settings', \"⚙️ Payment Methods\", self.show_payment_methods)" in line:
         # Insert after payment methods
         lines.insert(i+1, "            ('settings', \"🎨 Bill Design\", self.show_bill_designer),\n")
         found_map = True
         print("Added to Nav")
         break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print("✅ Bill Design integrated")
