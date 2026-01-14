
# Script to fix indentation of show_billing_terminal body in main.py
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
    
    # Check body indentation
    body_line_idx = start_idx + 1
    if body_line_idx < len(lines):
        body_indent = len(lines[body_line_idx]) - len(lines[body_line_idx].lstrip())
        def_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
        
        print(f"Def indent: {def_indent}, Body indent: {body_indent}")
        
        if body_indent == def_indent:
            print("Body needs indentation. Fixing...")
            
            # Determine end of function
            end_idx = len(lines)
            for i in range(body_line_idx, len(lines)):
                line = lines[i]
                if line.strip().startswith("def ") and (len(line) - len(line.lstrip()) == def_indent):
                     end_idx = i
                     break
            
            print(f"Block ends at line {end_idx}")
            
            # Apply indent
            for i in range(body_line_idx, end_idx):
                if lines[i].strip():
                    lines[i] = "    " + lines[i]
            
            with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print("✅ Body indentation fixed")
        else:
            print("Body indentation seems correct (> def indent)")
else:
    print("Function not found")
