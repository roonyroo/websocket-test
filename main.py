import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import threading

# Page config
st.set_page_config(
    page_title="WebSocket Test",
    page_icon="🔗",
    layout="wide"
)

# Initialize session state
if 'test_result' not in st.session_state:
    st.session_state.test_result = None
if 'test_running' not in st.session_state:
    st.session_state.test_running = False
if 'test_log' not in st.session_state:
    st.session_state.test_log = []

def add_log(message):
    """Add log message with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.test_log.append(f"[{timestamp}] {message}")

async def test_websocket():
    """Test WebSocket connection"""
    uri = "wss://stream.binance.com:9443/ws/!ticker@arr"
    
    add_log("Starting WebSocket test...")
    add_log(f"Connecting to: {uri}")
    
    try:
        async with websockets.connect(uri, ping_interval=20) as websocket:
            add_log("✅ Connected successfully!")
            
            # Receive one message to test
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(message)
            
            if isinstance(data, list):
                usdt_count = sum(1 for item in data if item.get('s', '').endswith('USDT'))
                add_log(f"📊 Received {usdt_count} USDT pairs")
                
                # Show first few USDT pairs
                usdt_pairs = [item for item in data if item.get('s', '').endswith('USDT')][:5]
                for pair in usdt_pairs:
                    symbol = pair['s']
                    price = pair['c']
                    add_log(f"  {symbol}: {price}")
            
            add_log("✅ Test completed successfully!")
            return True
            
    except asyncio.TimeoutError:
        add_log("❌ Connection timeout")
        return False
    except Exception as e:
        add_log(f"❌ Error: {str(e)}")
        return False

def run_test():
    """Run the WebSocket test"""
    st.session_state.test_running = True
    st.session_state.test_log = []
    
    def test_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_websocket())
            st.session_state.test_result = result
        finally:
            loop.close()
            st.session_state.test_running = False
    
    thread = threading.Thread(target=test_thread, daemon=True)
    thread.start()

# Main UI
st.title("WebSocket Connection Test")
st.markdown("**Testing Binance WebSocket Stream**")

# Test button
if st.button("Run WebSocket Test", type="primary", disabled=st.session_state.test_running):
    run_test()

# Status
if st.session_state.test_running:
    st.info("🔄 Test running...")
    st.rerun()
elif st.session_state.test_result is not None:
    if st.session_state.test_result:
        st.success("✅ WebSocket test PASSED")
    else:
        st.error("❌ WebSocket test FAILED")

# Test log
if st.session_state.test_log:
    st.subheader("Test Log")
    for log_entry in st.session_state.test_log:
        st.text(log_entry)

# Auto-refresh while test is running
if st.session_state.test_running:
    import time
    time.sleep(1)
    st.rerun()

st.markdown("---")
st.markdown("*Simple WebSocket connectivity test*")
