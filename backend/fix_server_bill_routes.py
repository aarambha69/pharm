
# Register Bill Design Routes
import re

file_path = 'backend/server.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
injected_require = False
injected_use = False

for line in lines:
    new_lines.append(line)
    
    # Inject require
    if "const dashboardRoutes = require('./dashboard_routes');" in line and not injected_require:
        new_lines.append("const billDesignRoutes = require('./bill_design_routes');\n")
        injected_require = True
        
    # Inject use
    if "app.use('/api', authenticateToken, dashboardRoutes);" in line and not injected_use:
        new_lines.append("app.use('/api', authenticateToken, billDesignRoutes);\n")
        injected_use = True

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
print("✅ Bill Design routes registered in server.js")
