# -*- coding: utf-8 -*-
"""
Multi-Beacon BLE RSSI Collector - Kết nối đồng thời đến nhiều beacons
"""
import pexpect
import time
from datetime import datetime
import threading
import json
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

# Biến toàn cục để lưu dữ liệu
beacon_data = {}  # {beacon_mac: {scanner_mac: {"rssi": value, "last_seen": timestamp, "count": number}}}
latest_readings = []  # Danh sách readings mới nhất
total_readings = 0
start_time = None
connection_status = {}  # Trạng thái kết nối của từng beacon

# Cấu hình
MAX_LATEST_READINGS = 1000
RECONNECT_DELAY = 5
STATS_INTERVAL = 30
CONNECTION_TIMEOUT = 15
NOTIFICATION_TIMEOUT = 30

def load_beacon_config():
    """Đọc cấu hình beacons từ file JSON"""
    try:
        with open('beancons.json', 'r') as f:
            config = json.load(f)
            return config['beacons']
    except Exception as e:
        print(f"Error loading beacon config: {e}")
        return []

def add_reading(scanner_mac, beacon_mac, rssi_value):
    """Thêm reading mới vào biến toàn cục"""
    global beacon_data, latest_readings, total_readings
    
    timestamp = datetime.now()
    
    # Cập nhật beacon_data theo cấu trúc: scanner -> detected_beacons
    if scanner_mac not in beacon_data:
        beacon_data[scanner_mac] = {}
    
    if beacon_mac not in beacon_data[scanner_mac]:
        beacon_data[scanner_mac][beacon_mac] = {
            "rssi": rssi_value, 
            "last_seen": timestamp, 
            "count": 1
        }
    else:
        beacon_data[scanner_mac][beacon_mac]["rssi"] = rssi_value
        beacon_data[scanner_mac][beacon_mac]["last_seen"] = timestamp
        beacon_data[scanner_mac][beacon_mac]["count"] += 1
    
    # Thêm vào latest_readings
    reading = {
        "timestamp": timestamp.isoformat(),
        "scanner_mac": scanner_mac,
        "detected_beacon": beacon_mac,
        "rssi": rssi_value
    }
    latest_readings.append(reading)
    
    # Giữ chỉ MAX_LATEST_READINGS readings mới nhất
    if len(latest_readings) > MAX_LATEST_READINGS:
        latest_readings.pop(0)
    
    total_readings += 1

def update_connection_status(beacon_mac, status, message=""):
    """Cập nhật trạng thái kết nối"""
    global connection_status
    connection_status[beacon_mac] = {
        "status": status,
        "last_update": datetime.now(),
        "message": message
    }

def get_stats():
    """Lấy thống kê hiện tại"""
    now = datetime.now()
    uptime = now - start_time if start_time else 0
    
    # Đếm số beacons được phát hiện
    total_detected_beacons = 0
    for scanner_data in beacon_data.values():
        total_detected_beacons += len(scanner_data)
    
    return {
        "total_scanners": len(beacon_data),
        "total_detected_beacons": total_detected_beacons,
        "total_readings": total_readings,
        "uptime_seconds": uptime.total_seconds() if uptime else 0,
        "connection_status": dict(connection_status),
        "scanner_data": dict(beacon_data),
        "latest_readings": latest_readings[-20:]  # 20 readings mới nhất
    }

def print_stats():
    """In thống kê ra console"""
    stats = get_stats()
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] MULTI-BEACON STATISTICS")
    print(f"{'='*80}")
    print(f"Uptime: {stats['uptime_seconds']:.1f} seconds")
    print(f"Active scanners: {stats['total_scanners']}")
    print(f"Total detected beacons: {stats['total_detected_beacons']}")
    print(f"Total readings: {stats['total_readings']}")
    
    print(f"\nConnection Status:")
    for mac, status in stats['connection_status'].items():
        last_update = status['last_update'].strftime("%H:%M:%S")
        print(f"  {mac}: {status['status']} (last: {last_update}) - {status['message']}")
    
    print(f"\nScanner Data:")
    for scanner_mac, detected_beacons in stats['scanner_data'].items():
        print(f"  Scanner {scanner_mac}:")
        for beacon_mac, data in detected_beacons.items():
            last_seen = data['last_seen'].strftime("%H:%M:%S")
            print(f"    └─ {beacon_mac}: RSSI={data['rssi']}, Count={data['count']}, Last={last_seen}")
    
    print(f"\nLatest 10 readings:")
    for reading in stats['latest_readings'][-10:]:
        timestamp = reading['timestamp'][-8:]  # Chỉ lấy time part
        print(f"  {timestamp} - {reading['scanner_mac']} detected {reading['detected_beacon']}: {reading['rssi']} dBm")

def stats_thread():
    """Thread để in stats định kỳ"""
    while True:
        time.sleep(STATS_INTERVAL)
        print_stats()

def connect_to_beacon(beacon_config):
    """Kết nối đến một beacon và thu thập dữ liệu"""
    mac_address = beacon_config['mac']
    notify_handle = beacon_config['notify_handle']
    
    print(f"[{datetime.now()}] Starting connection thread for {mac_address}")
    
    while True:
        try:
            update_connection_status(mac_address, "CONNECTING", "Attempting connection...")
            print(f"\n[{datetime.now()}] Connecting to {mac_address}...")
            
            child = pexpect.spawn("gatttool -I")
            child.expect(r"\[LE\]>", timeout=10)
            
            child.sendline(f"connect {mac_address}")
            child.expect("Connection successful", timeout=CONNECTION_TIMEOUT)
            
            update_connection_status(mac_address, "CONNECTED", "Connection established")
            print(f"[{datetime.now()}] Connected successfully to {mac_address}")
            
            # Enable notifications
            child.sendline(f"char-write-req {notify_handle} 0100")
            child.expect(r"\[LE\]>", timeout=5)
            
            update_connection_status(mac_address, "LISTENING", "Notifications enabled, listening for data")
            print(f"[{datetime.now()}] Notifications enabled for {mac_address} - Listening...")
            
            # Lắng nghe notifications
            while True:
                try:
                    child.expect(r"Notification handle = .*? \r", timeout=NOTIFICATION_TIMEOUT)
                    line = child.after.decode().strip()
                    
                    if "value:" in line:
                        hex_data = line.split("value:")[1].strip()
                        bytes_data = bytes.fromhex(hex_data)
                        
                        try:
                            decoded_str = bytes_data.decode("utf-8")
                            
                            # Parse beacon data: MAC,RSSI hoặc danh sách các beacons
                            # Format có thể là: "MAC1,RSSI1;MAC2,RSSI2;..."
                            beacon_entries = decoded_str.split(';')
                            
                            for entry in beacon_entries:
                                if ',' in entry:
                                    parts = entry.split(',')
                                    if len(parts) == 2:
                                        detected_beacon_mac = parts[0].strip()
                                        rssi = int(parts[1].strip())
                                        
                                        # Lưu vào biến toàn cục
                                        add_reading(mac_address, detected_beacon_mac, rssi)
                                        
                                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {mac_address} detected {detected_beacon_mac}: {rssi} dBm")
                            
                        except (UnicodeDecodeError, ValueError) as e:
                            print(f"[{datetime.now()}] Parse error from {mac_address}: {e}")
                            print(f"Raw hex data: {hex_data}")
                
                except pexpect.TIMEOUT:
                    update_connection_status(mac_address, "TIMEOUT", "No data received, checking connection")
                    print(f"[{datetime.now()}] Timeout from {mac_address} - checking connection...")
                    break
                
        except pexpect.TIMEOUT:
            update_connection_status(mac_address, "CONNECTION_FAILED", "Connection timeout")
            print(f"[{datetime.now()}] Connection timeout for {mac_address}")
        except Exception as e:
            update_connection_status(mac_address, "ERROR", str(e))
            print(f"[{datetime.now()}] Connection error for {mac_address}: {e}")
        
        print(f"[{datetime.now()}] Reconnecting to {mac_address} in {RECONNECT_DELAY} seconds...")
        time.sleep(RECONNECT_DELAY)

def collect_multi_beacon_data():
    """Thu thập dữ liệu từ nhiều beacons đồng thời"""
    global start_time
    start_time = datetime.now()
    
    # Đọc cấu hình beacons
    beacon_configs = load_beacon_config()
    if not beacon_configs:
        print("No beacon configuration found!")
        return
    
    print(f"[{start_time}] Starting Multi-Beacon BLE RSSI Collector...")
    print(f"Target beacons: {len(beacon_configs)}")
    for config in beacon_configs:
        print(f"  - {config['mac']} (handle: {config['notify_handle']})")
    
    # Bắt đầu stats thread
    stats_t = threading.Thread(target=stats_thread, daemon=True)
    stats_t.start()
    
    # Sử dụng ThreadPoolExecutor để quản lý nhiều connections
    with ThreadPoolExecutor(max_workers=len(beacon_configs)) as executor:
        # Khởi tạo connection threads cho từng beacon
        futures = []
        for config in beacon_configs:
            future = executor.submit(connect_to_beacon, config)
            futures.append(future)
        
        try:
            # Chờ tất cả threads hoàn thành (chúng sẽ chạy vô hạn)
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Thread error: {e}")
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Stopping all collectors...")
            executor.shutdown(wait=False)

def export_data_to_file():
    """Xuất dữ liệu ra file JSON"""
    data = {
        "export_time": datetime.now().isoformat(),
        "stats": get_stats(),
        "all_readings": latest_readings
    }
    
    filename = f"multi_beacon_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"Data exported to {filename}")

def main():
    """Hàm main"""
    try:
        collect_multi_beacon_data()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Stopping multi-beacon collector...")
        print_stats()
        
        # Hỏi có muốn xuất dữ liệu không
        try:
            export = input("\nExport data to JSON file? (y/n): ")
            if export.lower() == 'y':
                export_data_to_file()
        except:
            pass
        
        print("Goodbye!")

if __name__ == "__main__":
    main()
