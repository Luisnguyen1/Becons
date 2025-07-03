# -*- coding: utf-8 -*-
"""
Script để chạy cả BLE collector và Flask web server cùng lúc
"""
import threading
import time
from datetime import datetime

def run_ble_collector():
    """Chạy BLE collector trong thread riêng"""
    from easy import collect_ble_data
    try:
        collect_ble_data()
    except Exception as e:
        print(f"[{datetime.now()}] BLE Collector error: {e}")

def run_flask_app():
    """Chạy Flask app trong thread riêng"""
    from flask_app import app
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[{datetime.now()}] Flask App error: {e}")

if __name__ == "__main__":
    print("🚀 Starting BLE Beacons Monitor System...")
    print("="*60)
    
    # Bắt đầu BLE collector thread
    print("📡 Starting BLE Data Collector...")
    ble_thread = threading.Thread(target=run_ble_collector, daemon=True)
    ble_thread.start()
    
    # Đợi 3 giây để BLE collector khởi động
    time.sleep(3)
    
    # Bắt đầu Flask web server
    print("🌐 Starting Flask Web Server...")
    print("📱 Web interface: http://localhost:5000")
    print("📊 API Beacons: http://localhost:5000/api/beacons")
    print("📈 API Latest: http://localhost:5000/api/latest")
    print("="*60)
    print("⏹️  Press Ctrl+C to stop both services")
    
    try:
        run_flask_app()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Shutting down...")
        print("👋 Goodbye!")
