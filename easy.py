# -*- coding: utf-8 -*-
"""
Simple BLE RSSI collector - No database, just global variables
"""
import pexpect
import time
from datetime import datetime
import threading
import json

# Biến toàn cục để lưu dữ liệu
beacon_data = {}  # {mac_address: {"rssi": value, "last_seen": timestamp, "count": number}}
latest_readings = []  # Danh sách 100 readings mới nhất
total_readings = 0
start_time = None

# Cấu hình
MAC_ADDRESS = "C0:2C:ED:90:AD:A3"
NOTIFY_HANDLE = "0x0022"
MAX_LATEST_READINGS = 100

def add_reading(beacon_mac, rssi_value):
    """Thêm reading mới vào biến toàn cục"""
    global beacon_data, latest_readings, total_readings
    
    timestamp = datetime.now()
    
    # Cập nhật beacon_data
    if beacon_mac not in beacon_data:
        beacon_data[beacon_mac] = {"rssi": rssi_value, "last_seen": timestamp, "count": 1}
    else:
        beacon_data[beacon_mac]["rssi"] = rssi_value
        beacon_data[beacon_mac]["last_seen"] = timestamp
        beacon_data[beacon_mac]["count"] += 1
    
    # Thêm vào latest_readings
    reading = {
        "timestamp": timestamp.isoformat(),
        "beacon_mac": beacon_mac,
        "rssi": rssi_value
    }
    latest_readings.append(reading)
    
    # Giữ chỉ 100 readings mới nhất
    if len(latest_readings) > MAX_LATEST_READINGS:
        latest_readings.pop(0)
    
    total_readings += 1

def get_stats():
    """Lấy thống kê hiện tại"""
    now = datetime.now()
    uptime = now - start_time if start_time else 0
    
    return {
        "total_beacons": len(beacon_data),
        "total_readings": total_readings,
        "uptime_seconds": uptime.total_seconds() if uptime else 0,
        "beacons": dict(beacon_data),
        "latest_readings": latest_readings[-10:]  # 10 readings mới nhất
    }

def print_stats():
    """In thống kê ra console"""
    stats = get_stats()
    print(f"\n{'='*50}")
    print(f"[{datetime.now()}] STATISTICS")
    print(f"{'='*50}")
    print(f"Uptime: {stats['uptime_seconds']:.1f} seconds")
    print(f"Total beacons: {stats['total_beacons']}")
    print(f"Total readings: {stats['total_readings']}")
    print(f"\nBeacon Details:")
    
    for mac, data in stats['beacons'].items():
        last_seen = data['last_seen'].strftime("%H:%M:%S") if isinstance(data['last_seen'], datetime) else data['last_seen']
        print(f"  {mac}: RSSI={data['rssi']}, Count={data['count']}, Last={last_seen}")
    
    print(f"\nLatest 5 readings:")
    for reading in stats['latest_readings'][-5:]:
        timestamp = reading['timestamp'][-8:]  # Chỉ lấy time part
        print(f"  {timestamp} - {reading['beacon_mac']}: {reading['rssi']}")

def stats_thread():
    """Thread để in stats định kỳ"""
    while True:
        time.sleep(30)  # In stats mỗi 30 giây
        print_stats()

def collect_ble_data():
    """Thu thập dữ liệu BLE"""
    global start_time
    start_time = datetime.now()
    
    print(f"[{start_time}] Starting BLE RSSI Collector...")
    print(f"Target device: {MAC_ADDRESS}")
    print(f"Notify handle: {NOTIFY_HANDLE}")
    
    # Bắt đầu stats thread
    stats_t = threading.Thread(target=stats_thread, daemon=True)
    stats_t.start()
    
    while True:
        try:
            print(f"\n[{datetime.now()}] Connecting to {MAC_ADDRESS}...")
            
            child = pexpect.spawn("gatttool -I")
            child.expect(r"\[LE\]>", timeout=10)
            
            child.sendline(f"connect {MAC_ADDRESS}")
            child.expect("Connection successful", timeout=15)
            print(f"[{datetime.now()}] Connected successfully")
            
            # Enable notifications
            child.sendline(f"char-write-req {NOTIFY_HANDLE} 0100")
            child.expect(r"\[LE\]>", timeout=5)
            print(f"[{datetime.now()}] Notifications enabled - Listening...")
            
            # Lắng nghe notifications
            while True:
                try:
                    child.expect(r"Notification handle = .*? \r", timeout=30)
                    line = child.after.decode().strip()
                    
                    if "value:" in line:
                        hex_data = line.split("value:")[1].strip()
                        bytes_data = bytes.fromhex(hex_data)
                        
                        try:
                            decoded_str = bytes_data.decode("utf-8")
                            
                            # Parse beacon data: MAC,RSSI
                            parts = decoded_str.split(',')
                            if len(parts) == 2:
                                beacon_mac = parts[0].strip()
                                rssi = int(parts[1].strip())
                                
                                # Lưu vào biến toàn cục
                                add_reading(beacon_mac, rssi)
                                
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] {beacon_mac}: {rssi} dBm")
                            
                        except (UnicodeDecodeError, ValueError) as e:
                            print(f"[{datetime.now()}] Parse error: {e}")
                
                except pexpect.TIMEOUT:
                    print(f"[{datetime.now()}] Timeout - checking connection...")
                    break
                
        except Exception as e:
            print(f"[{datetime.now()}] Connection error: {e}")
            print("Reconnecting in 5 seconds...")
            time.sleep(5)

def export_data_to_file():
    """Xuất dữ liệu ra file JSON"""
    data = {
        "export_time": datetime.now().isoformat(),
        "stats": get_stats(),
        "all_readings": latest_readings
    }
    
    filename = f"ble_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"Data exported to {filename}")

if __name__ == "__main__":
    try:
        collect_ble_data()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Stopping collector...")
        print_stats()
        
        # Hỏi có muốn xuất dữ liệu không
        try:
            export = input("\nExport data to JSON file? (y/n): ")
            if export.lower() == 'y':
                export_data_to_file()
        except:
            pass
        
        print("Goodbye!")