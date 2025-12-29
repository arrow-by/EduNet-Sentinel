"""
Send Test NetFlow Packets - Simulates network traffic
"""
import socket
import struct
import time
import random

LISTENER_HOST = '127.0.0.1'
LISTENER_PORT = 2055

def ip_to_int(ip_str):
    """Convert IP address string to integer"""
    parts = ip_str.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])

def create_netflow_v5_packet(flows):
    """Create a NetFlow v5 packet with given flows"""
    # Header
    version = 5
    count = len(flows)
    sys_uptime = int(time.time() * 1000) & 0xFFFFFFFF
    unix_secs = int(time.time())
    unix_nsecs = 0
    flow_sequence = 0
    engine_type = 0
    engine_id = 0
    sampling = 0
    
    header = struct.pack('!HHIIIIBBH',
                        version, count, sys_uptime, unix_secs, unix_nsecs,
                        flow_sequence, engine_type, engine_id, sampling)
    
    # Flow records
    records = b''
    for flow in flows:
        record = struct.pack('!IIIHHIIIIHHxBBHHHHxx',
                           ip_to_int(flow['src_ip']),
                           ip_to_int(flow['dst_ip']),
                           0,  # next hop
                           0,  # input interface
                           0,  # output interface
                           flow['packets'],
                           flow['bytes'],
                           0,  # first switched
                           0,  # last switched
                           flow['src_port'],
                           flow['dst_port'],
                           flow['protocol'],
                           0,  # TCP flags
                           0,  # source AS
                           0,  # dest AS
                           0,  # source mask
                           0)  # dest mask
        records += record
    
    return header + records

def generate_sample_flows():
    """Generate sample flow data simulating various traffic patterns"""
    
    # Common web browsing patterns
    web_flows = [
        {
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8',
            'src_port': random.randint(49152, 65535),
            'dst_port': 53,
            'protocol': 17,  # UDP (DNS)
            'packets': random.randint(1, 5),
            'bytes': random.randint(100, 500)
        },
        {
            'src_ip': '192.168.1.100',
            'dst_ip': '142.250.185.78',  # Google
            'src_port': random.randint(49152, 65535),
            'dst_port': 443,
            'protocol': 6,  # TCP (HTTPS)
            'packets': random.randint(50, 200),
            'bytes': random.randint(5000, 50000)
        },
        {
            'src_ip': '192.168.1.101',
            'dst_ip': '104.16.132.229',  # Cloudflare
            'src_port': random.randint(49152, 65535),
            'dst_port': 443,
            'protocol': 6,  # TCP
            'packets': random.randint(30, 150),
            'bytes': random.randint(3000, 30000)
        },
    ]
    
    # SSH traffic (could be legitimate or scanning)
    ssh_flows = [
        {
            'src_ip': '192.168.1.105',
            'dst_ip': '192.168.1.200',
            'src_port': random.randint(49152, 65535),
            'dst_port': 22,
            'protocol': 6,  # TCP
            'packets': random.randint(10, 50),
            'bytes': random.randint(1000, 5000)
        }
    ]
    
    # ICMP ping
    icmp_flows = [
        {
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.4.4',
            'src_port': 0,
            'dst_port': 0,
            'protocol': 1,  # ICMP
            'packets': 4,
            'bytes': 256
        }
    ]
    
    return web_flows + ssh_flows + icmp_flows

def send_test_packets(num_packets=5, interval=2):
    """Send test NetFlow packets to the listener"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print("=" * 60)
    print("📤 NetFlow Test Packet Generator")
    print("=" * 60)
    print(f"Target: {LISTENER_HOST}:{LISTENER_PORT}")
    print(f"Sending {num_packets} packets with {interval}s interval\n")
    
    for i in range(num_packets):
        # Generate flows
        flows = generate_sample_flows()
        
        # Create packet
        packet = create_netflow_v5_packet(flows)
        
        # Send packet
        sock.sendto(packet, (LISTENER_HOST, LISTENER_PORT))
        
        print(f"✅ Sent packet {i+1}/{num_packets} ({len(packet)} bytes, {len(flows)} flows)")
        for flow in flows:
            print(f"   • {flow['src_ip']}:{flow['src_port']} → "
                  f"{flow['dst_ip']}:{flow['dst_port']} "
                  f"(proto {flow['protocol']}) - {flow['bytes']} bytes")
        
        if i < num_packets - 1:
            time.sleep(interval)
    
    sock.close()
    print(f"\n✅ Sent {num_packets} test packets successfully!")
    print(f"💡 Check the listener output and Grafana dashboards")

if __name__ == "__main__":
    # Send 5 test packets with 2-second intervals
    send_test_packets(num_packets=5, interval=2)