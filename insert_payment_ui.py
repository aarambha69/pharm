# Insert payment methods UI into main.py
with open('DesktopApp/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('DesktopApp/payment_methods_ui.py', 'r', encoding='utf-8') as pm:
    pm_content = pm.read()

# Insert before line 5907 (def run)
new_lines = lines[:5906] + ['\n' + pm_content + '\n'] + lines[5906:]

with open('DesktopApp/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✅ Payment methods UI functions added to main.py')
