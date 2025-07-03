# -*- coding: utf-8 -*-
"""
Flask Web App để hiển thị dữ liệu Multi-Beacon BLE RSSI
"""
from flask import Flask, render_template, jsonify
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Import multi-beacon collector
try:
    from run_monitor import multi_collector
except ImportError:
    multi_collector = None

@app.route('/')
def index():
    """Trang chính hiển thị dữ liệu multi-beacons"""
    return render_template('multi_beacon_index.html')

@app.route('/api/multi-beacons')
def api_multi_beacons():
    """API endpoint trả về dữ liệu từ tất cả beacons dạng JSON"""
    if not multi_collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'scanners': [],
            'total_scanners': 0,
            'total_detected_beacons': 0,
            'total_readings': 0,
            'uptime_seconds': 0,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
    
    try:
        stats = multi_collector.get_stats()
        
        # Format dữ liệu cho web interface
        scanners_data = []
        for scanner_mac, detected_beacons in stats['scanner_data'].items():
            scanner_info = {
                'scanner_mac': scanner_mac,
                'detected_beacons': [],
                'beacon_count': len(detected_beacons),
                'connection_status': stats['connection_status'].get(scanner_mac, {})
            }
            
            for beacon_mac, beacon_data in detected_beacons.items():
                beacon_info = {
                    'mac_address': beacon_mac,
                    'rssi': beacon_data['rssi'],
                    'count': beacon_data['count'],
                    'avg_rssi': beacon_data['avg_rssi'],
                    'min_rssi': beacon_data['min_rssi'],
                    'max_rssi': beacon_data['max_rssi'],
                    'last_seen': datetime.fromisoformat(beacon_data['last_seen']).strftime("%H:%M:%S"),
                    'first_seen': datetime.fromisoformat(beacon_data['first_seen']).strftime("%H:%M:%S")
                }
                scanner_info['detected_beacons'].append(beacon_info)
            
            # Sắp xếp beacons theo RSSI (mạnh nhất trước)
            scanner_info['detected_beacons'].sort(key=lambda x: x['rssi'], reverse=True)
            scanners_data.append(scanner_info)
        
        return jsonify({
            'scanners': scanners_data,
            'total_scanners': stats['total_scanners'],
            'total_detected_beacons': stats['total_detected_beacons'],
            'total_readings': stats['total_readings'],
            'uptime_seconds': int(stats['uptime_seconds']),
            'latest_readings': stats['latest_readings'][-15:],  # 15 readings mới nhất
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting stats: {str(e)}',
            'scanners': [],
            'total_scanners': 0,
            'total_detected_beacons': 0,
            'total_readings': 0,
            'uptime_seconds': 0,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })

@app.route('/api/scanner-status')
def api_scanner_status():
    """API endpoint trả về trạng thái kết nối của các scanners"""
    if not multi_collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'connection_status': {}
        })
    
    try:
        stats = multi_collector.get_stats()
        
        # Format connection status
        formatted_status = {}
        for scanner_mac, status in stats['connection_status'].items():
            formatted_status[scanner_mac] = {
                'status': status['status'],
                'message': status['message'],
                'last_update': datetime.fromisoformat(status['last_update']).strftime("%H:%M:%S")
            }
        
        return jsonify({
            'connection_status': formatted_status,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting scanner status: {str(e)}',
            'connection_status': {}
        })

@app.route('/api/latest-readings')
def api_latest_readings():
    """API endpoint trả về readings mới nhất từ tất cả scanners"""
    if not multi_collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'latest_readings': []
        })
    
    try:
        with multi_collector.stats_lock:
            # Lấy 50 readings mới nhất
            readings = [r.to_dict() for r in multi_collector.all_readings[-50:]]
        
        # Format readings cho web
        formatted_readings = []
        for reading in readings:
            formatted_readings.append({
                'timestamp': datetime.fromisoformat(reading['timestamp']).strftime("%H:%M:%S"),
                'scanner_mac': reading['scanner_mac'],
                'detected_beacon': reading['detected_beacon'],
                'rssi': reading['rssi']
            })
        
        return jsonify({
            'latest_readings': formatted_readings,
            'count': len(formatted_readings),
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting latest readings: {str(e)}',
            'latest_readings': []
        })

@app.route('/api/export')
def api_export():
    """API endpoint để export dữ liệu"""
    if not multi_collector:
        return jsonify({
            'success': False,
            'error': 'Multi-beacon collector not available'
        })
    
    try:
        filename = multi_collector.export_data()
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Data exported successfully to {filename}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        })

@app.route('/api/collector-control/<action>')
def api_collector_control(action):
    """API endpoint để điều khiển collector (start/stop)"""
    if not multi_collector:
        return jsonify({
            'success': False,
            'error': 'Multi-beacon collector not available'
        })
    
    try:
        if action == 'stop':
            multi_collector.stop()
            return jsonify({
                'success': True,
                'message': 'Collector stopped successfully'
            })
        elif action == 'status':
            return jsonify({
                'success': True,
                'running': multi_collector.running,
                'start_time': multi_collector.start_time.isoformat() if multi_collector.start_time else None
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown action: {action}'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Control action failed: {str(e)}'
        })

if __name__ == '__main__':
    print("🌐 Starting Multi-Beacon Flask Web Server...")
    print("📱 Access the web interface at: http://localhost:5000")
    print("📊 API endpoints:")
    print("   - http://localhost:5000/api/multi-beacons")
    print("   - http://localhost:5000/api/scanner-status")
    print("   - http://localhost:5000/api/latest-readings")
    print("   - http://localhost:5000/api/export")
    print("⏹️  Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
