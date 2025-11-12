#!/bin/bash

echo "🔄 Updating navigation bars in all templates..."

# List of all template files
TEMPLATES=("index.html" "topology.html" "config.html" "simulation.html" "devices.html" "analysis.html" "ml.html" "logs.html" "reports.html" "settings.html")

# New navbar code
NEW_NAVBAR='<nav class="navbar">
    <div class="nav-brand">
        <h1>🤖 AI Network Simulator</h1>
    </div>
    <div class="nav-links">
        <a href="/">Dashboard</a>
        <a href="/topology">Topology</a>
        <a href="/config">Configuration</a>
        <a href="/simulation">Simulation</a>
        <a href="/devices">Devices</a>
        <a href="/analysis">Analysis</a>
        <a href="/ml">AI/ML</a>
        <a href="/logs">Logs</a>
        <a href="/reports">Reports</a>
        <a href="/settings">Settings</a>
        
        <!-- User Info Section -->
        <div class="user-info">
            <span>Welcome, {{ user.name }}</span>
            <div class="user-dropdown">
                <button class="btn-user">�� {{ user.user }}</button>
                <div class="user-menu">
                    <a href="/settings" class="user-menu-item">⚙️ Settings</a>
                    <a href="/logout" class="user-menu-item">🚪 Logout</a>
                </div>
            </div>
        </div>
    </div>
</nav>'

# Update each template
for template in "${TEMPLATES[@]}"; do
    if [ -f "templates/$template" ]; then
        echo "📝 Updating $template..."
        
        # Create temporary file
        temp_file=$(mktemp)
        
        # Copy everything before nav
        sed -n '1,/^<nav class="navbar">/p' "templates/$template" | head -n -1 > "$temp_file"
        
        # Add new navbar
        echo "$NEW_NAVBAR" >> "$temp_file"
        
        # Copy everything after nav
        sed -n '/^<nav class="navbar">/,/^<\/nav>/!p' "templates/$template" | tail -n +2 >> "$temp_file"
        
        # Replace original file
        mv "$temp_file" "templates/$template"
        
        echo "✅ $template updated"
    else
        echo "❌ $template not found, skipping..."
    fi
done

echo "🎉 All templates updated successfully!"
