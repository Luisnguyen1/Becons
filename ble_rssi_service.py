# -*- coding: utf-8 -*-
import pexpect
import json
import time
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
import signal
import sys

class BLERSSIService:
    def __init__(self, config_file="config.json"):
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ble_rssi_service.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # InfluxDB setup
        self.influx_client = InfluxDBClient(
            url=self.config['influxdb']['url'],
            token=self.config['influxdb']['token'],
            org=self.config['influxdb']['org']
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        
        # BLE setup
        self.mac_address = self.config['ble']['mac_address']
        self.notify_handle = self.config['ble']['notify_handle']
        self.child = None
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.child:
            self.child.close()
        sys.exit(0)
    
    def connect_ble(self):
        """Connect to BLE device"""
        try:
            self.child = pexpect.spawn("gatttool -I")
            self.child.expect(r"\[LE\]>", timeout=10)
            
            self.logger.info(f"Connecting to {self.mac_address}")
            self.child.sendline(f"connect {self.mac_address}")
            self.child.expect("Connection successful", timeout=15)
            self.logger.info("BLE Connected successfully")
            
            # Enable notifications
            self.child.sendline(f"char-write-req {self.notify_handle} 0100")
            self.child.expect(r"\[LE\]>", timeout=5)
            self.logger.info("Notifications enabled")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to BLE device: {e}")
            return False
    
    def parse_beacon_data(self, decoded_str):
        """Parse beacon data to extract MAC and RSSI"""
        try:
            # Format: MAC_ADDRESS,RSSI (e.g., "5A:57:3B:FC:D5:23,-7")
            parts = decoded_str.split(',')
            if len(parts) == 2:
                mac = parts[0].strip()
                rssi = int(parts[1].strip())
                return mac, rssi
            return None, None
        except Exception as e:
            self.logger.error(f"Error parsing beacon data: {e}")
            return None, None
    
    def write_to_influxdb(self, beacon_mac, rssi):
        """Write RSSI data to InfluxDB"""
        try:
            point = Point("rssi_measurement") \
                .tag("beacon_mac", beacon_mac) \
                .tag("receiver_mac", self.mac_address) \
                .field("rssi", rssi) \
                .time(datetime.utcnow())
            
            self.write_api.write(
                bucket=self.config['influxdb']['bucket'],
                record=point
            )
            
            self.logger.info(f"Stored: {beacon_mac} -> RSSI: {rssi}")
            
        except Exception as e:
            self.logger.error(f"Failed to write to InfluxDB: {e}")
    
    def reconnect_ble(self):
        """Reconnect to BLE device"""
        self.logger.info("Attempting to reconnect...")
        if self.child:
            self.child.close()
        time.sleep(2)
        return self.connect_ble()
    
    def run(self):
        """Main service loop"""
        self.logger.info("Starting BLE RSSI Service")
        
        # Initial connection
        if not self.connect_ble():
            self.logger.error("Failed to establish initial BLE connection")
            return
        
        self.logger.info("Listening for beacon notifications...")
        consecutive_timeouts = 0
        max_timeouts = 3
        
        while self.running:
            try:
                self.child.expect(r"Notification handle = .*? \r", timeout=30)
                consecutive_timeouts = 0  # Reset timeout counter
                
                line = self.child.after.decode().strip()
                self.logger.debug(f"[RAW] {line}")
                
                if "value:" in line:
                    hex_data = line.split("value:")[1].strip()
                    bytes_data = bytes.fromhex(hex_data)
                    
                    try:
                        decoded_str = bytes_data.decode("utf-8")
                        self.logger.debug(f"[DECODED] {decoded_str}")
                        
                        # Parse and store beacon data
                        beacon_mac, rssi = self.parse_beacon_data(decoded_str)
                        if beacon_mac and rssi is not None:
                            self.write_to_influxdb(beacon_mac, rssi)
                        
                    except UnicodeDecodeError:
                        self.logger.debug(f"[DECODED] <binary> {bytes_data}")
                        
            except pexpect.TIMEOUT:
                consecutive_timeouts += 1
                self.logger.warning(f"Timeout waiting for notification ({consecutive_timeouts}/{max_timeouts})")
                
                if consecutive_timeouts >= max_timeouts:
                    self.logger.error("Too many consecutive timeouts, attempting reconnection")
                    if not self.reconnect_ble():
                        self.logger.error("Reconnection failed, exiting")
                        break
                    consecutive_timeouts = 0
                    
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                if not self.reconnect_ble():
                    self.logger.error("Reconnection failed, exiting")
                    break
        
        # Cleanup
        if self.child:
            self.child.close()
        self.influx_client.close()
        self.logger.info("Service stopped")

def main():
    service = BLERSSIService()
    service.run()

if __name__ == "__main__":
    main()
