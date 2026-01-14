
# Fix payment UI indent
with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i in range(len(lines)):
    line = lines[i]
    if "def show_add_payment_method_dialog(self):" in line:
        curr = len(line) - len(line.lstrip())
        if curr > 4:
            lines[i] = "    def show_add_payment_method_dialog(self):\n"
            count += 1
            print(f"Fixed add_payment definition at line {i+1}")
            
    elif "def show_upload_qr_dialog(self," in line:
        curr = len(line) - len(line.lstrip())
        if curr > 4:
            lines[i] = lines[i].lstrip() # Remove indent
            lines[i] = "    " + lines[i] # Add 4 spaces
            count += 1
            print(f"Fixed upload_qr definition at line {i+1}")
            
with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"✅ Fixed {count} function definitions")
