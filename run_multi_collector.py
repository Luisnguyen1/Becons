# -*- coding: utf-8 -*-
"""
Simple Multi-Beacon Runner - Chạy đơn giản trong console
"""
import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Kiểm tra và cài đặt requirements"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if requirements_file.exists():
        print("📦 Installing requirements...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
            print("✅ Requirements installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            return False
    else:
        print("⚠️  No requirements.txt found")
        return True

def run_console_collector():
    """Chạy collector trong console"""
    try:
        from advanced_multi_collector import main
        print("🚀 Starting console-based multi-beacon collector...")
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all files are in the same directory")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_web_collector():
    """Chạy collector với web interface"""
    try:
        print("🌐 Starting web-based multi-beacon collector...")
        print("Dashboard will be available at: http://localhost:5000")
        
        # Import và chạy
        from web_multi_collector import collector, run_flask
        import threading
        import time
        
        # Start Flask in a separate thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        print("📊 Starting collector...")
        if collector.start():
            print("✅ Collector started successfully")
            print("🌐 Web dashboard: http://localhost:5000")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                collector.stop()
                print("👋 Goodbye!")
        else:
            print("❌ Failed to start collector")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all files are in the same directory")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Menu chính"""
    print("🔍 Multi-Beacon BLE Collector")
    print("=" * 40)
    
    # Kiểm tra file config
    config_file = Path(__file__).parent / "beancons.json"
    if not config_file.exists():
        print("❌ Configuration file 'beancons.json' not found!")
        print("Please create the configuration file with your beacon settings.")
        return
    
    print("✅ Configuration file found")
    
    # Hiển thị menu
    print("\nSelect mode:")
    print("1. Console mode (simple text output)")
    print("2. Web dashboard mode (http://localhost:5000)")
    print("3. Install requirements only")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (0-3): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                if check_requirements():
                    run_console_collector()
                break
            elif choice == "2":
                if check_requirements():
                    run_web_collector()
                break
            elif choice == "3":
                check_requirements()
                break
            else:
                print("❌ Invalid choice. Please enter 0, 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
