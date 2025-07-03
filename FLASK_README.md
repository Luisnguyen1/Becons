# BLE Beacons Flask Monitor

## Mô tả
Flask web application đơn giản để hiển thị dữ liệu MAC address và RSSI từ các Bluetooth beacons.

## Cài đặt
```bash
pip install -r requirements.txt
```

## Các file quan trọng
- `easy.py` - BLE collector (thu thập dữ liệu từ beacons)
- `flask_app.py` - Flask web server
- `run_monitor.py` - Script chạy cả 2 service cùng lúc
- `templates/index.html` - Giao diện web

## Cách sử dụng

### Cách 1: Chạy cả BLE collector và web server (Khuyến nghị)
```bash
python run_monitor.py
```

### Cách 2: Chạy riêng biệt

#### Chạy BLE collector trước:
```bash
python easy.py
```

#### Trong terminal khác, chạy Flask app:
```bash
python flask_app.py
```

## Truy cập Web Interface
- Mở trình duyệt và vào: http://localhost:5000
- Hoặc truy cập từ thiết bị khác trong mạng: http://[IP_ADDRESS]:5000

## API Endpoints
- `GET /api/beacons` - Lấy danh sách tất cả beacons và thống kê
- `GET /api/latest` - Lấy 20 readings mới nhất

## Tính năng
✅ Hiển thị danh sách MAC addresses của beacons  
✅ Hiển thị RSSI (độ mạnh tín hiệu) theo thời gian thực  
✅ Đếm số lượng readings từ mỗi beacon  
✅ Hiển thị thời gian nhận tín hiệu cuối cùng  
✅ Giao diện web responsive, tự động cập nhật  
✅ API để lấy dữ liệu dạng JSON  
✅ Phân loại tín hiệu theo độ mạnh (màu sắc)  

## Cấu hình
Trong file `easy.py`, có thể thay đổi:
- `MAC_ADDRESS` - MAC address của thiết bị BLE chính
- `NOTIFY_HANDLE` - Handle để nhận notifications
- `MAX_LATEST_READINGS` - Số lượng readings lưu trữ tối đa

## Ghi chú
- Web interface tự động cập nhật mỗi 2 giây
- Hỗ trợ nhiều beacons cùng lúc
- Dữ liệu được lưu trong memory (không persistent)
- Có thể xuất dữ liệu ra file JSON khi dừng collector
