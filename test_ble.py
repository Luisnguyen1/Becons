# -*- coding: utf-8 -*-
"""
Simple test script to verify BLE RSSI service functionality
"""
import pexpect
import time
from datetime import datetime

def test_ble_connection():
    """Test BLE connection and data parsing"""
    mac_address = "C0:2C:ED:90:AD:A3"
    notify_handle = "0x0022"
    
    print(f"[{datetime.now()}] Testing BLE connection...")
    
    try:
        child = pexpect.spawn("gatttool -I")
        child.expect(r"\[LE\]>", timeout=10)
        
        print(f"[{datetime.now()}] Connecting to {mac_address}")
        child.sendline(f"connect {mac_address}")
        child.expect("Connection successful", timeout=15)
        print(f"[{datetime.now()}] Connected successfully")
        
        # Enable notifications
        child.sendline(f"char-write-req {notify_handle} 0100")
        child.expect(r"\[LE\]>", timeout=5)
        print(f"[{datetime.now()}] Notifications enabled")
        
        print(f"[{datetime.now()}] Listening for 60 seconds...")
        
        beacon_count = {}
        start_time = time.time()
        
        while time.time() - start_time < 60:  # Test for 60 seconds
            try:
                child.expect(r"Notification handle = .*? \r", timeout=10)
                line = child.after.decode().strip()
                
                if "value:" in line:
                    hex_data = line.split("value:")[1].strip()
                    bytes_data = bytes.fromhex(hex_data)
                    
                    try:
                        decoded_str = bytes_data.decode("utf-8")
                        print(f"[{datetime.now()}] DECODED: {decoded_str}")
                        
                        # Parse beacon data
                        parts = decoded_str.split(',')
                        if len(parts) == 2:
                            mac = parts[0].strip()
                            rssi = int(parts[1].strip())
                            
                            if mac not in beacon_count:
                                beacon_count[mac] = 0
                            beacon_count[mac] += 1
                            
                            print(f"  -> Beacon: {mac}, RSSI: {rssi}")
                        
                    except UnicodeDecodeError:
                        print(f"[{datetime.now()}] BINARY: {bytes_data}")
                        
            except pexpect.TIMEOUT:
                print(f"[{datetime.now()}] Timeout (10s)")
                continue
        
        child.close()
        
        print(f"\n[{datetime.now()}] Test Summary:")
        print(f"Total unique beacons detected: {len(beacon_count)}")
        for mac, count in beacon_count.items():
            print(f"  {mac}: {count} messages")
        
        if len(beacon_count) >= 3:
            print("✅ SUCCESS: Detected 3 or more beacons")
        else:
            print("⚠️  WARNING: Less than 3 beacons detected")
            
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")

if __name__ == "__main__":
    test_ble_connection()
