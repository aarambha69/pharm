
# Remove duplicate show_admin_dashboard
with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

definitions = []
for i, line in enumerate(lines):
    if "def show_admin_dashboard(self):" in line:
        definitions.append(i)

if len(definitions) > 1:
    to_remove_start = definitions[1] # The second one
    print(f"Removing duplicate at line {to_remove_start+1}")
    
    # Find end of this function
    to_remove_end = len(lines)
    for i in range(to_remove_start + 1, len(lines)):
        if lines[i].strip().startswith("def "):
            to_remove_end = i
            break
            
    print(f"Removing lines {to_remove_start+1} to {to_remove_end}")
    del lines[to_remove_start:to_remove_end]
    
    with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Duplicate removed")
else:
    print(f"Only {len(definitions)} definition found. No duplicates.")
