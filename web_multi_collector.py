# -*- coding: utf-8 -*-
"""
Flask Web Interface cho Multi-Beacon Collector
"""
from flask import Flask, render_template, jsonify
import threading
import time
from advanced_multi_collector import MultiBeaconCollector
import json
from datetime import datetime

app = Flask(__name__)
collector = MultiBeaconCollector()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """API endpoint để lấy stats hiện tại"""
    return jsonify(collector.get_stats())

@app.route('/api/start')
def start_collector():
    """API endpoint để start collector"""
    if not collector.running:
        success = collector.start()
        return jsonify({"success": success, "message": "Collector started" if success else "Failed to start collector"})
    else:
        return jsonify({"success": False, "message": "Collector already running"})

@app.route('/api/stop')
def stop_collector():
    """API endpoint để stop collector"""
    if collector.running:
        collector.stop()
        return jsonify({"success": True, "message": "Collector stopped"})
    else:
        return jsonify({"success": False, "message": "Collector not running"})

@app.route('/api/export')
def export_data():
    """API endpoint để export data"""
    try:
        filename = collector.export_data()
        return jsonify({"success": True, "filename": filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/readings')
def get_readings():
    """API endpoint để lấy latest readings"""
    with collector.stats_lock:
        readings = [r.to_dict() for r in collector.all_readings[-100:]]  # Latest 100 readings
    return jsonify(readings)

def run_flask():
    """Chạy Flask app"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🌐 Web dashboard available at: http://localhost:5000")
    print("📊 Starting collector...")
    
    try:
        if collector.start():
            print("✅ Collector started successfully")
            
            # Keep running
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        collector.stop()
        print("👋 Goodbye!")
