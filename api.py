#!/usr/bin/env python3
"""
Simple API для веб-интерфейса Trading Bot
"""

from flask import Flask, jsonify, request
import json
from datetime import datetime
import yaml

app = Flask(__name__)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Получить статус бота"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Получить историю сделок"""
    try:
        trades = []
        with open('logs/trades.json', 'r') as f:
            for line in f:
                trades.append(json.loads(line.strip()))
        return jsonify(trades)
    except:
        return jsonify([])

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Управление конфигурацией"""
    if request.method == 'GET':
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            return jsonify(config)
        except:
            return jsonify({})
    
    elif request.method == 'POST':
        config = request.json
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
