import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import threading

# Page config
st.set_page_config(
    page_title=\"WebSocket Test\",
    page_icon=\"🔗\",
    layout=\"wide\"
)

# Initialize session state
if 'test_result' not in st.session_state:
    st.session_state.test_result = None
if 'test_running' not in st.session_state:
    st.session_state.test_running = False
if 'test_log' not in st.session_state:
    st.session_state.test_log = []
if 'usdt_pairs' not in st.session_state:
    st.session_state.usdt_pairs = []

def add_log(message):
    \"\"\"Add log message with timestamp\"\"\"
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.test_log.append(f\"[{timestamp}] {message}\")

async def test_websocket():
    \"\"\"Test WebSocket connection with real data\"\"\"
    uri = \"wss://stream.binance.com:9443/ws/!ticker@arr\"
    
    add_log(\"Starting WebSocket test...\")
    add_log(f\"Connecting to: {uri}\")
    
    try:
        async with websockets.connect(uri, ping_interval=20) as websocket:
            add_log(\"✅ Connected successfully!\")
            
            # Receive one message to test
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(message)
            
            if isinstance(data, list):
                # Filter USDT pairs
                usdt_data = [item for item in data if item.get('s', '').endswith('USDT')]
                usdt_count = len(usdt_data)
                add_log(f\"📊 Received {usdt_count} USDT pairs\")
                
                # Get last 10 USDT pairs with real data
                last_10_usdt = usdt_data[-10:]
                st.session_state.usdt_pairs = []
                
                for pair in last_10_usdt:
                    symbol = pair['s']
                    current = float(pair['c'])
                    high = float(pair['h'])
                    low = float(pair['l'])
                    change = float(pair['P'])
                    
                    # Calculate profit margin
                    profit_margin = ((high - low) / low) * 100 if low > 0 else 0
                    
                    st.session_state.usdt_pairs.append({
                        'Symbol': symbol,
                        'Current': current,
                        'High': high,
                        'Low': low,
                        'Change %': change,
                        'Profit Margin %': round(profit_margin, 2)
                    })
                
                add_log(f\"📈 Captured last 10 USDT pairs with live data\")
            
            add_log(\"✅ Test completed successfully!\")
            return True
            
    except asyncio.TimeoutError:
        add_log(\"❌ Connection timeout\")
        return False
    except Exception as e:
        add_log(f\"❌ Error: {str(e)}\")
        return False

def run_test():
    \"\"\"Run the WebSocket test\"\"\"
    st.session_state.test_running = True
    st.session_state.test_log = []
    st.session_state.usdt_pairs = []
    
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
st.title(\"WebSocket Connection Test\")
st.markdown(\"**Testing Binance WebSocket Stream**\")

# Test button
if st.button(\"Run WebSocket Test\", type=\"primary\", disabled=st.session_state.test_running):
    run_test()

# Status
if st.session_state.test_running:
    st.info(\"🔄 Test running...\")
    st.rerun()
elif st.session_state.test_result is not None:
    if st.session_state.test_result:
        st.success(\"✅ WebSocket test PASSED\")
    else:
        st.error(\"❌ WebSocket test FAILED\")

# Real USDT data table
if st.session_state.usdt_pairs:
    st.subheader(\"Last 10 USDT Pairs (Live Data)\")
    
    # Create table
    import pandas as pd
    df = pd.DataFrame(st.session_state.usdt_pairs)
    st.dataframe(df, use_container_width=True)
    
    st.info(f\"Showing {len(st.session_state.usdt_pairs)} pairs with real-time data\")

# Test log
if st.session_state.test_log:
    st.subheader(\"Test Log\")
    for log_entry in st.session_state.test_log:
        st.text(log_entry)

# Auto-refresh while test is running
if st.session_state.test_running:
    import time
    time.sleep(1)
    st.rerun()

st.markdown(\"---\")
st.markdown(\"*WebSocket test with real USDT data*\")
