from influxdb_client import InfluxDBClient, Point
from datetime import datetime, timezone
import random

# InfluxDB connection details
url = "http://localhost:8086"
token = "-otWO-2ssGBlkE-k0KaIus4e5Qtk8-rsHVyvjg9sb6glgue2XGBtGzrzTGLqAVm0hu-2Tl5BXmuaaZyvdYH4Dg=="
org = "EduNetSentinel"
bucket = "network_flows"
# Create client
print("🔄 Connecting to InfluxDB...")
try:
    client = InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api()
    query_api = client.query_api()
    print("✅ Connected to InfluxDB")
except Exception as e:
    print(f"❌ Failed to connect to InfluxDB: {e}")
    exit(1)

# Test 1: Write sample flow data
print("\n🔄 Writing test data...")
try:
    point = Point("Network_flow") \
        .tag("source_ip", "192.168.1.100") \
        .tag("dest_ip", "8.8.8.8") \
        .tag("protocol", "TCP") \
        .tag("source_port", "45678") \
        .tag("dest_port", "443") \
        .field("bytes", random.randint(1000, 50000)) \
        .field("packets", random.randint(10, 100)) \
        .time(datetime.now(timezone.utc))
    
    write_api.write(bucket=bucket, record=point)
    print("✅ Successfully wrote test data to InfluxDB")
except Exception as e:
    print(f"❌ Error writing to InfluxDB: {e}")

# Test 2: Query the data back
print("\n🔄 Querying data...")
try:
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "network_flows")
        |> limit(n: 10)
    '''
    
    result = query_api.query(query=query)
    
    if result:
        print("\n📊 Recent flow records:")
        count = 0
        for table in result:
            for record in table.records:
                if count < 5:  # Show only first 5 records
                    print(f"  • {record.values.get('source_ip', 'N/A')} → {record.values.get('dest_ip', 'N/A')}: {record.values['_value']} {record.values['_field']}")
                    count += 1
        
        print(f"\n✅ Successfully queried {count} records from InfluxDB")
    else:
        print("⚠️  Query returned no results. This might be normal if this is your first run.")
        
except Exception as e:
    print(f"❌ Error querying InfluxDB: {e}")
    print("\n🔍 Troubleshooting tips:")
    print("  1. Check if your token is correct")
    print("  2. Verify org name matches your InfluxDB setup")
    print("  3. Verify bucket name exists in InfluxDB")
    print("  4. Check token permissions (should have read/write access)")

client.close()
print("\n🎉 Connection test complete!")
print("\n📝 Next steps:")
print("  1. If you see ✅ for both write and query, you're ready to proceed!")
print("  2. Go to http://localhost:8086 to view your data in InfluxDB UI")
print("  3. Go to http://localhost:3000 to set up Grafana dashboards")