#!/bin/bash

echo "🧹 Removing old environment..."
deactivate 2>/dev/null
rm -rf myenv
rm -rf ~/.cache/pip/

echo "🐍 Creating fresh environment..."
python3 -m venv myenv
source myenv/bin/activate

echo "📦 Installing packages in correct order..."
echo "1. Installing numpy..."
pip install numpy==1.24.3
python -c "import numpy; print('   ✅ Numpy:', numpy.__version__)"

echo "2. Installing pandas..."
pip install pandas==2.0.3
python -c "import pandas; print('   ✅ Pandas:', pandas.__version__)"

echo "3. Installing other packages..."
pip install matplotlib==3.7.2
pip install flask==2.3.3
pip install networkx==3.1

echo "✅ Final verification..."
python -c "
import numpy as np
import pandas as pd
import matplotlib
import flask
import networkx as nx
print('')
print('🎉 ALL PACKAGES WORKING!')
print('📊 Versions:')
print('   Numpy:', np.__version__)
print('   Pandas:', pd.__version__)
print('   Matplotlib:', matplotlib.__version__)
print('   Flask:', flask.__version__)
print('   NetworkX:', nx.__version__)
"

echo ""
echo "🚀 Now run: python app.py"