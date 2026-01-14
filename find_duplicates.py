
# Find duplicate functions
filename = 'DesktopApp/main.py'
with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = []
for i, line in enumerate(lines):
    if "def show_admin_dashboard(self):" in line:
        found.append(i+1)

print(f"show_admin_dashboard found at lines: {found}")
