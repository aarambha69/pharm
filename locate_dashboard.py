
with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def show_super_admin_dashboard(self):" in line:
        print(f"Found function at line {i+1}")
        # Print first few lines to confirm
        print(lines[i+1][:100])
