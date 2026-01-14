
# Script to replace show_billing_terminal in main.py
import re

with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open('DesktopApp/billing_terminal_impl.py', 'r', encoding='utf-8') as f:
    new_code = f.read()

# Remove imports line if present (should not be)
new_code = new_code.replace("import customtkinter as ctk\n", "")

# Regex to find the old show_billing_terminal function
# It starts at line 4542 in my previous view.
# It ends before `def show_system_logs(self):` at line 4562.
pattern = r"def show_billing_terminal\(self\):[\s\S]*?(?=\n    def show_system_logs)"

# Find match
match = re.search(pattern, content)

if match:
    start_index = match.start()
    end_index = match.end()
    
    new_content = content[:start_index] + new_code + content[end_index:]
    
    with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Successfully replaced billing terminal function")
else:
    print("❌ Could not find show_billing_terminal to replace")
