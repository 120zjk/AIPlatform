import os
import sys
import subprocess
from pathlib import Path

def ensure_dependencies():
    required_packages = [
        'Flask==2.3.3',
        'flask-cors==4.0.0', 
        'python-dotenv==1.0.0',
        'requests==2.31.0',
        'Werkzeug==2.3.7'
    ]
    for package in required_packages:
        try:
            package_name = package.split('==')[0].replace('-', '_')
            __import__(package_name)
        except ImportError:
            print(f"Installing {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
ensure_dependencies()

# 添加 backend 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 導入應用
from app import app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))

    app.run(host='0.0.0.0', port=port, debug=False)
