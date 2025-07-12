import asyncio
import websockets
import json
from datetime import datetime

async def test_binance_websocket():
    """Simple test of Binance WebSocket connection"""
    uri = "wss://stream.binance.com:9443/ws/!ticker@arr"
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to Binance WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected successfully!")
            
            # Receive a few messages to test
            for i in range(3):
                message = await websocket.recv()
                data = json.loads(message)
                
                # Count USDT pairs
                if isinstance(data, list):
                    usdt_count = sum(1 for item in data if item.get('s', '').endswith('USDT'))
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Message {i+1}: {usdt_count} USDT pairs received")
                    
                    # Show a sample USDT pair
                    for item in data:
                        if item.get('s', '').endswith('USDT'):
                            symbol = item['s']
                            price = item['c']
                            high = item['h']
                            low = item['l']
                            print(f"  Sample: {symbol} - Price: {price}, High: {high}, Low: {low}")
                            break
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Message {i+1}: Single ticker data")
                
                # Wait a bit between messages
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        return False
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Test completed successfully!")
    return True

if __name__ == "__main__":
    print("=== Binance WebSocket Test ===")
    success = asyncio.run(test_binance_websocket())
    
    if success:
        print("✅ WebSocket connection test PASSED")
    else:
        print("❌ WebSocket connection test FAILED")
