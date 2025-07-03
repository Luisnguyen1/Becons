# -*- coding: utf-8 -*-
"""
Script để chạy Multi-Beacon Flask App với Location Mapping
"""
import sys
import os
import threading
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask_app_multi import app, set_collector

def run_web_app():
    """Chạy Flask web application"""
    print("🌐 Starting Multi-Beacon Flask Web Server with Location Mapping...")
    print("📱 Main Monitor: http://localhost:5000")
    print("🗺️ Location Map: http://localhost:5000/map")
    print("📊 API endpoints:")
    print("   - http://localhost:5000/api/multi-beacons")
    print("   - http://localhost:5000/api/positioning-data")
    print("   - http://localhost:5000/api/beacon-distances")
    print("   - http://localhost:5000/api/scanner-status")
    print("   - http://localhost:5000/api/latest-readings")
    print("   - http://localhost:5000/api/export")
    print("⏹️  Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_with_mock_data():
    """Chạy với dữ liệu mock để test interface"""
    import json
    from datetime import datetime, timedelta
    import random
    
    class MockCollector:
        def __init__(self):
            self.running = True
            self.start_time = datetime.now()
            self.all_readings = []
            
            # Mock data for 3 target beacons
            self.target_beacons = [
                '80:4B:50:56:A6:91',  # Beacon 1
                '60:A4:23:C9:85:C1',  # Beacon 2  
                'C0:2C:ED:90:AD:A3'   # Beacon 3
            ]
            
            # Mock scanner MAC
            self.mock_scanner = '00:1A:2B:3C:4D:5E'
            
            # Generate some mock readings
            self._generate_mock_readings()
        
        def _generate_mock_readings(self):
            """Generate mock RSSI readings"""
            base_time = datetime.now() - timedelta(minutes=5)
            
            for i in range(100):
                timestamp = base_time + timedelta(seconds=i*3)
                for beacon_mac in self.target_beacons:
                    # Simulate realistic RSSI values (-40 to -90 dBm)
                    base_rssi = random.randint(-90, -40)
                    rssi = base_rssi + random.randint(-5, 5)  # Add some variation
                    
                    reading = MockReading(
                        timestamp=timestamp.isoformat(),
                        scanner_mac=self.mock_scanner,
                        detected_beacon=beacon_mac,
                        rssi=rssi
                    )
                    self.all_readings.append(reading)
        
        def get_stats(self):
            """Return mock stats data"""
            now = datetime.now()
            uptime = (now - self.start_time).total_seconds()
            
            # Create mock scanner data
            scanner_data = {
                self.mock_scanner: {}
            }
            
            # Group readings by beacon
            for beacon_mac in self.target_beacons:
                beacon_readings = [r for r in self.all_readings if r.detected_beacon == beacon_mac]
                
                if beacon_readings:
                    rssis = [r.rssi for r in beacon_readings]
                    latest_reading = max(beacon_readings, key=lambda x: x.timestamp)
                    
                    scanner_data[self.mock_scanner][beacon_mac] = {
                        'rssi': latest_reading.rssi,
                        'count': len(beacon_readings),
                        'avg_rssi': sum(rssis) / len(rssis),
                        'min_rssi': min(rssis),
                        'max_rssi': max(rssis),
                        'last_seen': latest_reading.timestamp,
                        'first_seen': min(beacon_readings, key=lambda x: x.timestamp).timestamp
                    }
            
            return {
                'total_scanners': 1,
                'total_detected_beacons': len(self.target_beacons),
                'total_readings': len(self.all_readings),
                'uptime_seconds': uptime,
                'scanner_data': scanner_data,
                'connection_status': {
                    self.mock_scanner: {
                        'status': 'Connected',
                        'message': 'Mock scanner active',
                        'last_update': now.isoformat()
                    }
                },
                'latest_readings': self.all_readings[-15:]
            }
        
        def export_data(self):
            """Mock export function"""
            filename = f"mock_beacon_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            return filename
        
        def stop(self):
            """Stop the mock collector"""
            self.running = False
    
    class MockReading:
        def __init__(self, timestamp, scanner_mac, detected_beacon, rssi):
            self.timestamp = timestamp
            self.scanner_mac = scanner_mac
            self.detected_beacon = detected_beacon
            self.rssi = rssi
        
        def to_dict(self):
            return {
                'timestamp': self.timestamp,
                'scanner_mac': self.scanner_mac,
                'detected_beacon': self.detected_beacon,
                'rssi': self.rssi
            }
    
    # Create and set mock collector
    mock_collector = MockCollector()
    set_collector(mock_collector)
    
    print("🔄 Running with MOCK DATA for testing...")
    print("📝 Mock data includes 3 target beacons with simulated RSSI values")
    
    # Start web app
    run_web_app()

if __name__ == '__main__':
    print("🚀 Multi-Beacon Location Mapping System")
    print("=" * 50)
    
    # Check if we want to run with mock data
    if len(sys.argv) > 1 and sys.argv[1] == '--mock':
        run_with_mock_data()
    else:
        print("ℹ️  To run with mock data: python run_location_app.py --mock")
        print("ℹ️  To run with real collector, start your beacon collector first")
        run_web_app()
