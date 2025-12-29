"""
Test entire NetFlow system
"""
from influxdb_client import InfluxDBClient
import socket
import time

print("=" * 60)
print("🧪 SYSTEM TEST")
print("=" * 60)

# Test 1: InfluxDB Connection
print("\n1️⃣ Testing InfluxDB connection...")
try:
    client = InfluxDBClient(
        url="http://localhost:8086",
        token="-otWO-2ssGBlkE-k0KaIus4e5Qtk8-rsHVyvjg9sb6glgue2XGBtGzrzTGLqAVm0hu-2Tl5BXmuaaZyvdYH4Dg==",  # UPDATE THIS
        org="EduNetSentinel"       # UPDATE THIS
    )
    health = client.health()
    print(f"✅ InfluxDB is {health.status}")
    client.close()
except Exception as e:
    print(f"❌ InfluxDB connection failed: {e}")

# Test 2: Port availability
print("\n2️⃣ Testing if port 2055 is available...")
try:
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_sock.bind(('0.0.0.0', 2055))
    print("✅ Port 2055 is available")
    test_sock.close()
except Exception as e:
    print(f"❌ Port 2055 not available: {e}")

# Test 3: UDP send/receive
print("\n3️⃣ Testing UDP communication...")
try:
    # Receiver
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(('127.0.0.1', 3000))
    recv_sock.settimeout(2)
    
    # Sender
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_sock.sendto(b"TEST", ('127.0.0.1', 3000))
    
    data, addr = recv_sock.recvfrom(1024)
    print(f"✅ UDP communication works: received '{data.decode()}'")
    
    recv_sock.close()
    send_sock.close()
except Exception as e:
    print(f"❌ UDP test failed: {e}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETE")
print("=" * 60)