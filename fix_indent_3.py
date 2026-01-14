
# Script to fix indentation of ENTIRE show_billing_terminal block in main.py
import re

with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "def show_billing_terminal(self):" in line:
        start_idx = i
    elif "def show_system_logs(self):" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Found function range: {start_idx + 1} to {end_idx}")
    
    # Indent everything between start_idx+1 and end_idx
    count = 0
    for i in range(start_idx + 1, end_idx):
        if lines[i].strip():
            # Check if it was already indented by previous script?
            # Previous script indented lines 4543-4591.
            # Lines 4591 onwards (nested functions) are at 4 spaces.
            # Lines 4543-4591 are now at 8 spaces.
            
            # Wait, if I indent blindly, 4543-4591 will become 12 spaces!
            # I should only indent if indent is 4 spaces.
            
            curr_indent = len(lines[i]) - len(lines[i].lstrip())
            if curr_indent == 4:
                lines[i] = "    " + lines[i]
                count += 1
                
    print(f"Indented {count} lines")
    
    with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Full block indentation fixed")
else:
    print("Could not find start/end markers")
