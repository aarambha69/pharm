
# Script to replace payment methods functions in main.py
import re

with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open('DesktopApp/enhanced_payment_ui.py', 'r', encoding='utf-8') as f:
    new_code = f.read()

# Remove the import line if present in new code
new_code = new_code.replace("from tkinter import messagebox, ttk, StringVar, IntVar, DoubleVar, BooleanVar, filedialog\n", "")

# Regex to find the old show_add_payment_method_dialog
pattern_add = r"def show_add_payment_method_dialog\(self\):[\s\S]*?(?=\n    def show_upload_qr_dialog)"
match_add = re.search(pattern_add, content)

# Regex to find the old show_upload_qr_dialog
pattern_qr = r"def show_upload_qr_dialog\(self, method\):[\s\S]*?(?=\n    def run\(self\))"
match_qr = re.search(pattern_qr, content)

if match_add and match_qr:
    # We replace both blocks with the new code
    start_index = match_add.start()
    end_index = match_qr.end()
    
    # Check if there is extra indentation in the new code or if we need to add it
    # The new code is likely at root level indentation, main.py functions are inside a class (indent 4)
    indented_code = ""
    for line in new_code.splitlines():
        if line.strip():
            indented_code += line + "\n"
        else:
            indented_code += "\n"
            
    # Actually the previously generated file has indentation corresponding to method level?
    # Let's check indentation of new code
    # The new code was written as methods: "    def show..."
    
    new_content = content[:start_index] + new_code + content[end_index:]
    
    with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Successfully replaced payment UI functions")
else:
    print("❌ Could not find functions to replace")
    if not match_add: print("- show_add_payment_method_dialog not found")
    if not match_qr: print("- show_upload_qr_dialog not found")
