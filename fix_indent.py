
# Script to fix indentation of show_billing_terminal in main.py
import re

with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with show_billing_terminal
start_idx = -1
for i, line in enumerate(lines):
    if "def show_billing_terminal(self):" in line:
        start_idx = i
        break

if start_idx != -1:
    print(f"Found function at line {start_idx + 1}")
    
    # Check indentation
    current_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    print(f"Current indentation: {current_indent}")
    
    if current_indent > 4:
        # Dedent by (current_indent - 4)
        dedent_amt = current_indent - 4
        print(f"Dedenting by {dedent_amt} spaces")
        
        # Determine end of function - strict check for next function def at 4 spaces
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip().startswith("def ") and (len(line) - len(line.lstrip()) == 4):
                 end_idx = i
                 break
        
        print(f"Block ends at line {end_idx}")
        
        # Apply dedent
        for i in range(start_idx, end_idx):
            if lines[i].strip(): # Only dedent non-empty lines
                if len(lines[i]) - len(lines[i].lstrip()) >= dedent_amt:
                     lines[i] = lines[i][dedent_amt:]
        
        with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ Indentation fixed")
    else:
        print("Indentation seems correct (<= 4)")
else:
    print("Function not found")
