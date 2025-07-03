# -*- coding: utf-8 -*-
"""
Flask Web App để hiển thị dữ liệu BLE RSSI từ beacons
"""
from flask import Flask, render_template, jsonify
from datetime import datetime
import threading
import time
from easy import beacon_data, latest_readings, get_stats, total_readings, start_time

app = Flask(__name__)

@app.route('/')
def index():
    """Trang chính hiển thị dữ liệu beacons"""
    return render_template('index.html')

@app.route('/api/beacons')
def api_beacons():
    """API endpoint trả về dữ liệu beacons dạng JSON"""
    stats = get_stats()
    
    # Format dữ liệu cho dễ hiển thị
    beacons_list = []
    for mac, data in stats['beacons'].items():
        beacon_info = {
            'mac_address': mac,
            'rssi': data['rssi'],
            'count': data['count'],
            'last_seen': data['last_seen'].strftime("%H:%M:%S") if isinstance(data['last_seen'], datetime) else str(data['last_seen'])
        }
        beacons_list.append(beacon_info)
    
    # Sắp xếp theo RSSI (mạnh nhất trước)
    beacons_list.sort(key=lambda x: x['rssi'], reverse=True)
    
    return jsonify({
        'beacons': beacons_list,
        'total_beacons': stats['total_beacons'],
        'total_readings': stats['total_readings'],
        'uptime_seconds': int(stats['uptime_seconds']),
        'latest_readings': stats['latest_readings'][-10:],  # 10 readings mới nhất
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })

@app.route('/api/latest')
def api_latest():
    """API endpoint trả về readings mới nhất"""
    return jsonify({
        'latest_readings': latest_readings[-20:],  # 20 readings mới nhất
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })

if __name__ == '__main__':
    print("🌐 Starting Flask Web Server...")
    print("📱 Access the web interface at: http://localhost:5000")
    print("📊 API endpoints:")
    print("   - http://localhost:5000/api/beacons")
    print("   - http://localhost:5000/api/latest")
    print("⏹️  Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
