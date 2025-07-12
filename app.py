import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import threading
import pandas as pd

# Page config
st.set_page_config(
    page_title=\"WebSocket Test\",
    page_icon=\"🔗\",
    layout=\"wide\"
)

# Initialize session state with connection management
if 'ws_connected' not in st.session_state:
    st.session_state.ws_connected = False
if 'ws_data' not in st.session_state:
    st.session_state.ws_data = []
if 'ws_status' not in st.session_state:
    st.session_state.ws_status = \"Disconnected\"
if 'ws_thread' not in st.session_state:
    st.session_state.ws_thread = None
if 'stop_websocket' not in st.session_state:
    st.session_state.stop_websocket = False

def add_log(message):
    \"\"\"Add timestamped log message\"\"\"
    timestamp = datetime.now().strftime('%H:%M:%S')
    if 'ws_logs' not in st.session_state:
        st.session_state.ws_logs = []
    st.session_state.ws_logs.append(f\"[{timestamp}] {message}\")
    # Keep only last 20 logs
    if len(st.session_state.ws_logs) > 20:
        st.session_state.ws_logs = st.session_state.ws_logs[-20:]

async def websocket_handler():
    \"\"\"Handle WebSocket connection with proper cleanup\"\"\"
    uri = \"wss://stream.binance.com:9443/ws/!ticker@arr\"
    
    try:
        add_log(\"Attempting WebSocket connection...\")
        st.session_state.ws_status = \"Connecting\"
        
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
            add_log(\"✅ Connected to Binance WebSocket\")
            st.session_state.ws_connected = True
            st.session_state.ws_status = \"Connected\"
            
            # Listen for messages until stop signal
            while not st.session_state.stop_websocket:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if isinstance(data, list):
                        # Filter USDT pairs
                        usdt_data = [item for item in data if item.get('s', '').endswith('USDT')]
                        
                        # Process top 10 USDT pairs
                        processed_data = []
                        for pair in usdt_data[:10]:
                            try:
                                symbol = pair['s']
                                current = float(pair['c'])
                                high = float(pair['h'])
                                low = float(pair['l'])
                                change = float(pair['P'])
                                
                                if low > 0:
                                    # Calculate LD: % difference from current to low
                                    ld = ((current - low) / low) * 100
                                    # Calculate HD: % difference from current to high  
                                    hd = ((current - high) / high) * 100
                                    # Calculate Profit margin: (high - low) / low * 100
                                    profit_margin = ((high - low) / low) * 100
                                    
                                    processed_data.append({
                                        'Symbol': symbol,
                                        'LD': round(ld, 2),
                                        'HD': round(hd, 2),
                                        '% Profit': round(profit_margin, 2)
                                    })
                            except (ValueError, KeyError):
                                continue
                        
                        st.session_state.ws_data = processed_data
                        add_log(f\"📊 Updated {len(processed_data)} USDT pairs\")
                        
                except asyncio.TimeoutError:
                    # Timeout is expected for stop signal checking
                    continue
                except websockets.exceptions.ConnectionClosed:
                    add_log(\"❌ WebSocket connection closed\")
                    break
                    
    except Exception as e:
        add_log(f\"❌ WebSocket error: {str(e)}\")
    finally:
        st.session_state.ws_connected = False
        st.session_state.ws_status = \"Disconnected\"
        add_log(\"WebSocket connection closed\")

def start_websocket():
    \"\"\"Start WebSocket in separate thread\"\"\"
    if not st.session_state.ws_connected and (st.session_state.ws_thread is None or not st.session_state.ws_thread.is_alive()):
        st.session_state.stop_websocket = False
        
        def websocket_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(websocket_handler())
            finally:
                loop.close()
        
        st.session_state.ws_thread = threading.Thread(target=websocket_thread, daemon=True)
        st.session_state.ws_thread.start()
        add_log(\"🚀 Starting WebSocket connection...\")

def stop_websocket():
    \"\"\"Stop WebSocket connection\"\"\"
    st.session_state.stop_websocket = True
    st.session_state.ws_connected = False
    st.session_state.ws_status = \"Disconnected\"
    add_log(\"🛑 Stopping WebSocket connection...\")

# Main UI
st.title(\"Binance USDT WebSocket Test\")
st.markdown(\"**Real-time USDT pair analysis with WebSocket connection**\")

# Connection controls
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button(\"🚀 Start\", disabled=st.session_state.ws_connected):
        start_websocket()

with col2:
    if st.button(\"🛑 Stop\", disabled=not st.session_state.ws_connected):
        stop_websocket()

with col3:
    if st.session_state.ws_status == \"Connected\":
        st.success(f\"Status: {st.session_state.ws_status}\")
    elif st.session_state.ws_status == \"Connecting\":
        st.warning(f\"Status: {st.session_state.ws_status}\")
    else:
        st.info(f\"Status: {st.session_state.ws_status}\")

# Data display
if st.session_state.ws_data:
    st.subheader(\"Live USDT Pairs\")
    df = pd.DataFrame(st.session_state.ws_data)
    st.dataframe(df, use_container_width=True)
    
    # Show summary
    st.info(f\"Showing {len(st.session_state.ws_data)} pairs with real-time data\")

# Logs display
if 'ws_logs' in st.session_state and st.session_state.ws_logs:
    st.subheader(\"Connection Log\")
    for log_entry in st.session_state.ws_logs[-10:]:  # Show last 10 logs
        st.text(log_entry)

# Auto-refresh for live updates
if st.session_state.ws_connected:
    st.rerun()

st.markdown(\"---\")
st.markdown(\"*WebSocket test with connection management*\")
