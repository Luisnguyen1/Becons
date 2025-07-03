# -*- coding: utf-8 -*-
"""
Flask Web App đơn giản với dữ liệu mẫu để test giao diện
"""
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import random
import time

app = Flask(__name__)

# Dữ liệu mẫu để test
sample_beacons = {
    "A1:B2:C3:D4:E5:F6": {"rssi": -45, "last_seen": datetime.now(), "count": 156},
    "B2:C3:D4:E5:F6:A1": {"rssi": -67, "last_seen": datetime.now() - timedelta(seconds=5), "count": 89},
    "C3:D4:E5:F6:A1:B2": {"rssi": -78, "last_seen": datetime.now() - timedelta(seconds=12), "count": 234}
}

sample_readings = []
start_time = datetime.now()

# Tạo dữ liệu readings mẫu
for i in range(20):
    mac = random.choice(list(sample_beacons.keys()))
    rssi = random.randint(-80, -40)
    timestamp = datetime.now() - timedelta(seconds=i*5)
    sample_readings.append({
        "timestamp": timestamp.isoformat(),
        "beacon_mac": mac,
        "rssi": rssi
    })

sample_readings.reverse()  # Sắp xếp theo thời gian tăng dần

@app.route('/')
def index():
    """Trang chính hiển thị dữ liệu beacons"""
    return render_template('index.html')

@app.route('/api/beacons')
def api_beacons():
    """API endpoint trả về dữ liệu beacons dạng JSON"""
    # Cập nhật RSSI ngẫu nhiên để mô phỏng dữ liệu thay đổi
    for mac in sample_beacons:
        # Thay đổi RSSI một chút để mô phỏng
        current_rssi = sample_beacons[mac]["rssi"]
        new_rssi = current_rssi + random.randint(-3, 3)
        new_rssi = max(-90, min(-30, new_rssi))  # Giới hạn trong khoảng hợp lý
        sample_beacons[mac]["rssi"] = new_rssi
        sample_beacons[mac]["count"] += random.randint(0, 2)
        
        # Cập nhật thời gian nếu có reading mới
        if random.random() < 0.7:  # 70% chance có reading mới
            sample_beacons[mac]["last_seen"] = datetime.now()
    
    # Format dữ liệu cho dễ hiển thị
    beacons_list = []
    for mac, data in sample_beacons.items():
        beacon_info = {
            'mac_address': mac,
            'rssi': data['rssi'],
            'count': data['count'],
            'last_seen': data['last_seen'].strftime("%H:%M:%S")
        }
        beacons_list.append(beacon_info)
    
    # Sắp xếp theo RSSI (mạnh nhất trước)
    beacons_list.sort(key=lambda x: x['rssi'], reverse=True)
    
    uptime = (datetime.now() - start_time).total_seconds()
    total_readings = sum(data['count'] for data in sample_beacons.values())
    
    return jsonify({
        'beacons': beacons_list,
        'total_beacons': len(sample_beacons),
        'total_readings': total_readings,
        'uptime_seconds': int(uptime),
        'latest_readings': sample_readings[-10:],  # 10 readings mới nhất
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })

@app.route('/api/latest')
def api_latest():
    """API endpoint trả về readings mới nhất"""
    # Thêm reading mới ngẫu nhiên
    if random.random() < 0.8:  # 80% chance thêm reading mới
        mac = random.choice(list(sample_beacons.keys()))
        rssi = sample_beacons[mac]["rssi"] + random.randint(-2, 2)
        new_reading = {
            "timestamp": datetime.now().isoformat(),
            "beacon_mac": mac,
            "rssi": rssi
        }
        sample_readings.append(new_reading)
        
        # Giữ chỉ 30 readings mới nhất
        if len(sample_readings) > 30:
            sample_readings.pop(0)
    
    return jsonify({
        'latest_readings': sample_readings[-20:],  # 20 readings mới nhất
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })

if __name__ == '__main__':
    print("🌐 Starting Flask Demo Web Server...")
    print("📱 Access the web interface at: http://localhost:5000")
    print("📊 This is a DEMO version with sample data")
    print("📡 To use real BLE data, run: python run_monitor.py")
    print("⏹️  Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
