"""
NetFlow Listener - Receives and parses NetFlow v5 packets
"""
import socket
import struct
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB Configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "-otWO-2ssGBlkE-k0KaIus4e5Qtk8-rsHVyvjg9sb6glgue2XGBtGzrzTGLqAVm0hu-2Tl5BXmuaaZyvdYH4Dg=="  # Replace with your actual token
INFLUX_ORG = "EduNetSentinel"
INFLUX_BUCKET = "network_flows"

# NetFlow Configuration
NETFLOW_PORT = 2055
BUFFER_SIZE = 1500  # Standard MTU size

class NetFlowV5Parser:
    """Parse NetFlow v5 packets"""
    
    # NetFlow v5 Header: 24 bytes
    HEADER_FORMAT = '!HHIIIIBBH'
    HEADER_SIZE = 24
    
    # NetFlow v5 Flow Record: 48 bytes
    RECORD_FORMAT = '!IIIHHIIIIHHBBBBHHBBH'
    RECORD_SIZE = 48

    
    def __init__(self):
        self.packets_received = 0
        self.flows_parsed = 0
    
    def parse_packet(self, data):
        """Parse a NetFlow v5 packet and return list of flow records"""
        if len(data) < self.HEADER_SIZE:
            print(f"⚠️  Packet too small: {len(data)} bytes")
            return []
        
        # Parse header
        header = struct.unpack(self.HEADER_FORMAT, data[:self.HEADER_SIZE])
        version = header[0]
        count = header[1]
        
        if version != 5:
            print(f"⚠️  Unsupported NetFlow version: {version}")
            return []
        
        self.packets_received += 1
        print(f"📦 Received NetFlow packet: {count} flows")
        
        # Parse flow records
        flows = []
        offset = self.HEADER_SIZE
        
        for i in range(count):
            if offset + self.RECORD_SIZE > len(data):
                print(f"⚠️  Incomplete flow record at offset {offset}")
                break
            
            record_data = data[offset:offset + self.RECORD_SIZE]
            flow = self.parse_flow_record(record_data)
            if flow:
                flows.append(flow)
                self.flows_parsed += 1
            
            offset += self.RECORD_SIZE
        
        return flows
    
    def parse_flow_record(self, data):
        """Parse a single flow record"""
        try:
            record = struct.unpack(self.RECORD_FORMAT, data)
            
            # Extract fields
            source_ip = self.int_to_ip(record[0])
            dest_ip = self.int_to_ip(record[1])
            source_port = record[4]
            dest_port = record[5]
            protocol = record[11]
            packets = record[10]
            bytes_count = record[7]
            
            # Map protocol number to name
            protocol_name = self.get_protocol_name(protocol)
            
            flow = {
                'source_ip': source_ip,
                'dest_ip': dest_ip,
                'source_port': source_port,
                'dest_port': dest_port,
                'protocol': protocol_name,
                'protocol_number': protocol,
                'packets': packets,
                'bytes': bytes_count,
                'timestamp': datetime.now(timezone.utc)
            }
            
            return flow
            
        except Exception as e:
            print(f"❌ Error parsing flow record: {e}")
            return None
    
    @staticmethod
    def int_to_ip(ip_int):
        """Convert integer to IP address string"""
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
    
    @staticmethod
    def get_protocol_name(protocol_num):
        """Map protocol number to name"""
        protocols = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP',
            47: 'GRE',
            50: 'ESP',
            51: 'AH',
            89: 'OSPF'
        }
        return protocols.get(protocol_num, f'PROTO_{protocol_num}')


class NetFlowListener:
    """Listen for NetFlow packets and store to InfluxDB"""
    
    def __init__(self):
        self.parser = NetFlowV5Parser()
        self.socket = None
        
        # Initialize InfluxDB client
        self.influx_client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        print("✅ Connected to InfluxDB")
    
    def start(self):
        """Start listening for NetFlow packets"""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', NETFLOW_PORT))
            
            print(f"🎧 Listening for NetFlow packets on port {NETFLOW_PORT}...")
            print(f"💡 To test, run: python send_test_netflow.py")
            print(f"⏹️  Press Ctrl+C to stop\n")
            
            while True:
                # Receive packet
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                print(f"\n📡 Received packet from {addr[0]}:{addr[1]} ({len(data)} bytes)")
                
                # Parse packet
                flows = self.parser.parse_packet(data)
                
                # Store flows to InfluxDB
                if flows:
                    self.store_flows(flows)
                    print(f"✅ Stored {len(flows)} flows to InfluxDB")
                    print(f"📊 Total: {self.parser.packets_received} packets, {self.parser.flows_parsed} flows")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping NetFlow listener...")
            self.cleanup()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.cleanup()
    
    def store_flows(self, flows):
        """Store flows to InfluxDB"""
        points = []
        
        for flow in flows:
            point = Point("network_flows") \
                .tag("source_ip", flow['source_ip']) \
                .tag("dest_ip", flow['dest_ip']) \
                .tag("protocol", flow['protocol']) \
                .tag("source_port", str(flow['source_port'])) \
                .tag("dest_port", str(flow['dest_port'])) \
                .field("bytes", flow['bytes']) \
                .field("packets", flow['packets']) \
                .time(flow['timestamp'])
            
            points.append(point)
            
            # Print flow details
            print(f"  🔹 {flow['source_ip']}:{flow['source_port']} → "
                  f"{flow['dest_ip']}:{flow['dest_port']} "
                  f"({flow['protocol']}) - {flow['bytes']} bytes, {flow['packets']} packets")
        
        try:
            self.write_api.write(bucket=INFLUX_BUCKET, record=points)
        except Exception as e:
            print(f"❌ Error writing to InfluxDB: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.socket:
            self.socket.close()
        if self.influx_client:
            self.influx_client.close()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 EduNet Sentinel - NetFlow Listener")
    print("=" * 60)
    
    listener = NetFlowListener()
    listener.start()