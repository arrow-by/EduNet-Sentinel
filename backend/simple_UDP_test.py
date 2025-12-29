import socket

# Simple UDP receiver
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 2055))
print("🎧 Listening on port 2055...")
print("Waiting for data...\n")

while True:
    data, addr = sock.recvfrom(1024)
    print(f"✅ Received {len(data)} bytes from {addr}")
    print(f"Data: {data[:50]}...")  # Show first 50 bytes