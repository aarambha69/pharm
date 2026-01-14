
# Fix server.js routes
import re

file_path = 'backend/server.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Collect requires that need to be at top
requires_to_add = set()
requires_to_add.add("const purchaseRoutes = require('./purchase_routes');")
requires_to_add.add("const paymentMethodsRoutes = require('./payment_methods_routes');")
requires_to_add.add("const dashboardRoutes = require('./dashboard_routes');")

# 2. Filter out existing top-level requires to avoid duplication
new_lines = []
existing_requires = set()

# We will rewrite the file line by line
header_phase = True
for line in lines:
    stripped = line.strip()
    if stripped.startswith("const") and "require" in stripped and "routes" in stripped:
        existing_requires.add(stripped)
    
    # Detect the bad block start
    if "app.use('/api', authenticateToken, (req, res, next) => {" in line:
        # We found the mess. We will skip lines until we see Profile Management or similar
        header_phase = False
        continue
        
    if not header_phase:
        # We are skipping the bad block.
        # Check if we reached the next section
        if "// Profile Management" in line:
            header_phase = True
            # Now insert the CLEAN block
            new_lines.append("// --- AUTHENTICATED ROUTES ---\n")
            new_lines.append("app.use('/api', authenticateToken, purchaseRoutes);\n")
            new_lines.append("app.use('/api', authenticateToken, paymentMethodsRoutes);\n")
            new_lines.append("app.use('/api', authenticateToken, dashboardRoutes);\n")
            new_lines.append("\n")
            new_lines.append(line) # The profile line
        continue
        
    # In header phase, keep lines but filter duplicated requires/bad requires
    if header_phase:
        # If it's one of our target requires, skip it (we will add them all at once at specific place)
        if any(req in line for req in requires_to_add):
            continue
        new_lines.append(line)

# 3. Inject requires at the top (after dotenv)
final_lines = []
injected = False
for line in new_lines:
    final_lines.append(line)
    if "require('dotenv').config();" in line and not injected:
        for req in requires_to_add:
            final_lines.append(req + "\n")
        injected = True

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("✅ Server.js cleaned up")
