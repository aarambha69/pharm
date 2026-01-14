
# Fix nested functions indentation
with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = -1
end = -1

for i, line in enumerate(lines):
    if "def update_cart_display():" in line:
        start = i
        print(f"Start found at {i+1}")
    elif "def show_system_logs(self):" in line:
        if start != -1: # Only match if we found start
            end = i
            print(f"End found at {i+1}")
            break

if start != -1 and end != -1:
    print(f"Indenting lines {start+1} to {end}")
    count = 0
    for i in range(start, end):
        if lines[i].strip():
            lines[i] = "    " + lines[i]
            count += 1
            
    with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Fixed indentation for {count} lines")
else:
    print("Markers not found")
