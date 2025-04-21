#!/usr/bin/env python3
"""
データベースマイグレーションスクリプト
実際の処理はbackend/migrate.pyで行われます
"""
import os
import sys
import subprocess

# スクリプトのパスを取得
script_path = os.path.dirname(os.path.abspath(__file__))
backend_migrate = os.path.join(script_path, 'backend', 'migrate.py')

print("backend/migrate.pyを実行します...")
result = subprocess.call([sys.executable, backend_migrate])
sys.exit(result) 