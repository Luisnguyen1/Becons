#!/bin/bash

echo "Installing BLE RSSI Service dependencies..."

# Update system
sudo apt update

# Install required system packages
sudo apt install -y python3-pip python3-dev bluez bluez-tools

# Install Python packages
pip3 install --user pexpect influxdb-client

# Create service directory if it doesn't exist
sudo mkdir -p /opt/ble-rssi-service

# Copy service files
sudo cp ble_rssi_service.py /opt/ble-rssi-service/
sudo cp config.json /opt/ble-rssi-service/
sudo cp ble-rssi.service /etc/systemd/system/

# Set permissions
sudo chmod +x /opt/ble-rssi-service/ble_rssi_service.py
sudo chown -R root:root /opt/ble-rssi-service/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ble-rssi.service

echo "Installation complete!"
echo "Please edit /opt/ble-rssi-service/config.json with your InfluxDB settings"
echo "Then start the service with: sudo systemctl start ble-rssi.service"
echo "Check status with: sudo systemctl status ble-rssi.service"
echo "View logs with: sudo journalctl -u ble-rssi.service -f"
