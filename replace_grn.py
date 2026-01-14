import sys

# Read the new function
with open('DesktopApp/grn_rebuild.py', 'r', encoding='utf-8') as f:
    new_function = f.read()

# Read the original file
with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find function boundaries
start_line = 5316  # 0-indexed, so line 5317
end_line = 5566    # 0-indexed, so line 5567

# Replace the function
new_lines = lines[:start_line] + [new_function + '\n'] + lines[end_line:]

# Write back
with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Replaced lines {start_line+1} to {end_line} with new function ({len(new_function.splitlines())} lines)")
