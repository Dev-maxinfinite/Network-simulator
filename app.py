from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
import re
import os
from datetime import datetime
import csv
import hashlib
import json

app = Flask(__name__)
app.secret_key = 'network-simulator-secret-key-2024'

# ==================== AUTHENTICATION SYSTEM ====================
users = {
    'admin': {
        'password': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',  # 'password'
        'role': 'admin',
        'name': 'Administrator'
    },
    'user': {
        'password': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',  # 'password'
        'role': 'user', 
        'name': 'Regular User'
    }
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== DATA MANAGEMENT ====================
def init_csv_files():
    """Initialize all CSV files with sample data"""
    os.makedirs('data', exist_ok=True)
    os.makedirs('configs', exist_ok=True)
    
    # Devices CSV
    if not os.path.exists('data/devices.csv'):
        df_devices = pd.DataFrame([
            {'name': 'R1', 'device_type': 'router', 'ip_address': '192.168.1.1', 'status': 'active', 'cpu_usage': 25, 'memory_usage': 40, 'interfaces': 2, 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'name': 'R2', 'device_type': 'router', 'ip_address': '10.0.0.2', 'status': 'active', 'cpu_usage': 30, 'memory_usage': 45, 'interfaces': 2, 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'name': 'SW1', 'device_type': 'switch', 'ip_address': 'N/A', 'status': 'active', 'cpu_usage': 15, 'memory_usage': 35, 'interfaces': 3, 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ])
        df_devices.to_csv('data/devices.csv', index=False)
    
    # Topology CSV
    if not os.path.exists('data/topology.csv'):
        df_topology = pd.DataFrame([
            {'source': 'R1', 'target': 'SW1', 'source_interface': 'GigabitEthernet0/0', 'target_interface': 'GigabitEthernet1/1', 'bandwidth': 1000, 'status': 'active'},
            {'source': 'R1', 'target': 'R2', 'source_interface': 'GigabitEthernet0/1', 'target_interface': 'GigabitEthernet0/0', 'bandwidth': 1000, 'status': 'active'}
        ])
        df_topology.to_csv('data/topology.csv', index=False)
    
    # Simulation Results CSV
    if not os.path.exists('data/simulation_results.csv'):
        df_simulations = pd.DataFrame(columns=['timestamp', 'simulation_type', 'duration', 'results', 'status'])
        df_simulations.to_csv('data/simulation_results.csv', index=False)
    
    # Logs CSV
    if not os.path.exists('data/logs.csv'):
        df_logs = pd.DataFrame(columns=['timestamp', 'level', 'device', 'message', 'source'])
        df_logs.to_csv('data/logs.csv', index=False)
    
    # Create sample config files
    create_sample_configs()

def create_sample_configs():
    """Create sample configuration files"""
    configs = {
        'R1-config.txt': """hostname R1
!
interface GigabitEthernet0/0
 description Connected to SW1 interface GigabitEthernet1/1
 ip address 192.168.1.1 255.255.255.0
 mtu 1500
 speed 1000
!
interface GigabitEthernet0/1
 description Connected to R2 interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.252
 mtu 1500
 speed 1000
!
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
 network 10.0.0.0 0.0.0.3 area 0
!
! Connected to SW1 interface GigabitEthernet1/1
! Connected to R2 interface GigabitEthernet0/0""",
        
        'R2-config.txt': """hostname R2
!
interface GigabitEthernet0/0
 description Connected to R1 interface GigabitEthernet0/1
 ip address 10.0.0.2 255.255.255.252
 mtu 1500
 speed 1000
!
interface GigabitEthernet0/1
 description Connected to Internet
 ip address 203.0.113.1 255.255.255.0
 mtu 1500
 speed 1000
!
router ospf 1
 network 10.0.0.0 0.0.0.3 area 0
!
! Connected to R1 interface GigabitEthernet0/1""",
        
        'SW1-config.txt': """hostname SW1
!
interface GigabitEthernet1/1
 description Connected to R1 interface GigabitEthernet0/0
 switchport mode access
!
interface GigabitEthernet1/2
 description Connected to PC1
 switchport mode access
!
interface GigabitEthernet1/3
 description Connected to PC2
 switchport mode access
!
vlan 10
 name Users
!
vlan 20
 name Servers
!
! Connected to R1 interface GigabitEthernet0/0"""
    }
    
    for filename, content in configs.items():
        if not os.path.exists(f'configs/{filename}'):
            with open(f'configs/{filename}', 'w') as f:
                f.write(content)

# ==================== NETWORK TOPOLOGY GENERATOR ====================
class NetworkTopology:
    def __init__(self):
        self.graph = nx.Graph()
    
    def parse_config(self, config_text):
        """Parse Cisco-like configuration"""
        config = {
            'hostname': 'unknown',
            'interfaces': {},
            'device_type': 'router'
        }
        
        # Extract hostname
        hostname_match = re.search(r'hostname\s+(\S+)', config_text)
        if hostname_match:
            config['hostname'] = hostname_match.group(1)
        
        # Detect device type
        if 'vlan' in config_text.lower() and 'switch' in config_text.lower():
            config['device_type'] = 'switch'
        
        # Extract interfaces
        interface_blocks = re.split(r'interface\s+', config_text)[1:]
        for block in interface_blocks:
            lines = block.split('\n')
            iface_name = lines[0].strip()
            iface_config = {}
            
            # IP Address
            ip_match = re.search(r'ip address\s+(\S+)\s+(\S+)', block)
            if ip_match:
                iface_config['ip_address'] = ip_match.group(1)
                iface_config['subnet_mask'] = ip_match.group(2)
            
            # Description (neighbor info)
            desc_match = re.search(r'description\s+(.+)', block)
            if desc_match:
                iface_config['description'] = desc_match.group(1)
                # Extract neighbor from description
                neighbor_match = re.search(r'Connected to\s+(\S+)', desc_match.group(1))
                if neighbor_match:
                    iface_config['neighbor'] = neighbor_match.group(1)
            
            config['interfaces'][iface_name] = iface_config
        
        return config
    
    def generate_topology(self):
        """Generate topology from config files"""
        self.graph.clear()
        
        # Load all config files
        config_files = [f for f in os.listdir('configs') if f.endswith('.txt')]
        devices = {}
        
        for config_file in config_files:
            with open(f'configs/{config_file}', 'r') as f:
                config_text = f.read()
                device_name = config_file.replace('-config.txt', '')
                devices[device_name] = self.parse_config(config_text)
        
        # Add nodes
        for device_name, config in devices.items():
            self.graph.add_node(device_name, **config)
        
        # Add edges based on neighbor relationships
        for device_name, config in devices.items():
            for iface_name, iface_config in config['interfaces'].items():
                if 'neighbor' in iface_config:
                    neighbor = iface_config['neighbor']
                    if neighbor in devices:
                        self.graph.add_edge(
                            device_name, 
                            neighbor,
                            interface=iface_name,
                            bandwidth=1000
                        )
        
        return self.graph
    
    def visualize_topology(self):
        """Create topology visualization"""
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph)
        
        # Node colors based on device type
        node_colors = []
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            if node_data.get('device_type') == 'router':
                node_colors.append('lightblue')
            elif node_data.get('device_type') == 'switch':
                node_colors.append('lightgreen')
            else:
                node_colors.append('orange')
        
        nx.draw(self.graph, pos, with_labels=True, node_color=node_colors, 
                node_size=1500, font_size=8, font_weight='bold', edge_color='gray')
        
        # Save to bytes
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
        img.seek(0)
        plt.close()
        
        return base64.b64encode(img.getvalue()).decode()

# ==================== AI/ML FEATURES ====================
class AIModels:
    @staticmethod
    def detect_anomalies(network_data):
        """Simple anomaly detection"""
        anomalies = []
        for device, data in network_data.items():
            if data.get('cpu_usage', 0) > 80:
                anomalies.append(f"High CPU usage on {device}: {data['cpu_usage']}%")
            if data.get('memory_usage', 0) > 85:
                anomalies.append(f"High Memory usage on {device}: {data['memory_usage']}%")
            if data.get('status') == 'inactive':
                anomalies.append(f"Device {device} is inactive")
        return anomalies
    
    @staticmethod
    def predict_traffic(historical_data):
        """Simple traffic prediction"""
        return "Traffic expected to be normal with peak during 2PM-6PM"

# ==================== ROUTES ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == hash_password(password):
            session['user'] = username
            session['role'] = users[username]['role']
            session['name'] = users[username]['name']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Load stats for dashboard
    try:
        df_devices = pd.read_csv('data/devices.csv')
        df_topology = pd.read_csv('data/topology.csv')
        
        stats = {
            'total_devices': len(df_devices),
            'active_devices': len(df_devices[df_devices['status'] == 'active']),
            'total_links': len(df_topology),
            'network_health': 95  # Placeholder
        }
    except:
        stats = {'total_devices': 0, 'active_devices': 0, 'total_links': 0, 'network_health': 0}
    
    return render_template('index.html', user=session, stats=stats)

@app.route('/topology')
@login_required
def topology_page():
    return render_template('topology.html', user=session)

@app.route('/config')
@login_required
def config_page():
    return render_template('config.html', user=session)

@app.route('/simulation')
@login_required
def simulation_page():
    return render_template('simulation.html', user=session)

@app.route('/devices')
@login_required
def devices_page():
    return render_template('devices.html', user=session)

@app.route('/analysis')
@login_required
def analysis_page():
    return render_template('analysis.html', user=session)

@app.route('/ml')
@login_required
def ml_page():
    return render_template('ml.html', user=session)

@app.route('/logs')
@login_required
def logs_page():
    return render_template('logs.html', user=session)

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html', user=session)

@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html', user=session)

# ==================== API ROUTES ====================
@app.route('/api/topology')
@login_required
def api_topology():
    graph = topology.generate_topology()
    
    # Convert to JSON format
    nodes = [{'id': node, **data} for node, data in graph.nodes(data=True)]
    links = [{'source': u, 'target': v, **data} for u, v, data in graph.edges(data=True)]
    
    # Generate topology image
    topology_img = topology.visualize_topology()
    
    return jsonify({
        'nodes': nodes,
        'links': links,
        'topology_image': topology_img
    })

@app.route('/api/devices')
@login_required
def api_devices():
    try:
        df = pd.read_csv('data/devices.csv')
        return jsonify(df.to_dict('records'))
    except:
        return jsonify([])

@app.route('/api/validate-config', methods=['POST'])
@login_required
def validate_config():
    config_text = request.json.get('config', '')
    device_name = request.json.get('device_name', 'unknown')
    
    # Save config file
    with open(f'configs/{device_name}-config.txt', 'w') as f:
        f.write(config_text)
    
    # Parse and validate
    config = topology.parse_config(config_text)
    
    # Simple validation
    errors = []
    warnings = []
    
    if config['hostname'] == 'unknown':
        warnings.append("Hostname not found in configuration")
    
    if not config['interfaces']:
        warnings.append("No interfaces configured")
    
    # Update devices CSV
    try:
        df = pd.read_csv('data/devices.csv')
        if device_name not in df['name'].values:
            new_device = {
                'name': device_name,
                'device_type': config['device_type'],
                'ip_address': list(config['interfaces'].values())[0].get('ip_address', 'N/A') if config['interfaces'] else 'N/A',
                'status': 'active',
                'cpu_usage': 0,
                'memory_usage': 0,
                'interfaces': len(config['interfaces']),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            df = pd.concat([df, pd.DataFrame([new_device])], ignore_index=True)
            df.to_csv('data/devices.csv', index=False)
    except Exception as e:
        print(f"Error updating devices: {e}")
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'config': config
    })

@app.route('/api/start-simulation', methods=['POST'])
@login_required
def start_simulation():
    simulation_type = request.json.get('type', 'basic')
    
    # Generate sample simulation data
    devices_data = {}
    try:
        df_devices = pd.read_csv('data/devices.csv')
        for device in df_devices['name'].tolist():
            devices_data[device] = {
                'cpu_usage': 20 + (hash(device) % 50),  # Random between 20-70
                'memory_usage': 30 + (hash(device) % 40),
                'status': 'active',
                'packets_processed': 1000 + (hash(device) % 9000)
            }
    except:
        # Fallback data
        devices_data = {
            'R1': {'cpu_usage': 65, 'memory_usage': 45, 'status': 'active', 'packets_processed': 5000},
            'R2': {'cpu_usage': 45, 'memory_usage': 35, 'status': 'active', 'packets_processed': 3000},
            'SW1': {'cpu_usage': 25, 'memory_usage': 25, 'status': 'active', 'packets_processed': 8000}
        }
    
    # Detect anomalies
    anomalies = ai_models.detect_anomalies(devices_data)
    
    # Save simulation results
    try:
        df_simulations = pd.read_csv('data/simulation_results.csv')
        new_simulation = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'simulation_type': simulation_type,
            'duration': 60,
            'results': json.dumps({'devices': devices_data, 'anomalies': anomalies}),
            'status': 'completed'
        }
        df_simulations = pd.concat([df_simulations, pd.DataFrame([new_simulation])], ignore_index=True)
        df_simulations.to_csv('data/simulation_results.csv', index=False)
    except Exception as e:
        print(f"Error saving simulation: {e}")
    
    return jsonify({
        'status': 'running',
        'devices': devices_data,
        'anomalies': anomalies,
        'message': f'{simulation_type} simulation started'
    })

@app.route('/api/network-analysis')
@login_required
def network_analysis():
    graph = topology.generate_topology()
    
    analysis = {
        'total_devices': len(graph.nodes()),
        'total_links': len(graph.edges()),
        'network_density': nx.density(graph),
        'is_connected': nx.is_connected(graph),
        'average_degree': sum(dict(graph.degree()).values()) / len(graph.nodes()) if graph.nodes() else 0
    }
    
    return jsonify(analysis)

@app.route('/api/ml-predict', methods=['POST'])
@login_required
def ml_predict():
    data = request.json
    prediction = ai_models.predict_traffic(data)
    return jsonify({'prediction': prediction})

@app.route('/api/logs')
@login_required
def api_logs():
    try:
        df_logs = pd.read_csv('data/logs.csv')
        return jsonify(df_logs.to_dict('records'))
    except:
        return jsonify([])

# ==================== INITIALIZATION ====================
# Initialize components
init_csv_files()
topology = NetworkTopology()
ai_models = AIModels()

if __name__ == '__main__':
    print("🚀 Starting AI Network Simulator...")
    print("🌐 Server running on http://localhost:5000")
    print("📧 Login with: admin / password")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)