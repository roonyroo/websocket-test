import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import threading
import pandas as pd

# Page config
st.set_page_config(
    page_title=\"Binance USDT Tracker\",
    page_icon=\"📊\",
    layout=\"wide\"
)

# Initialize session state
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
    if len(st.session_state.ws_logs) > 20:
        st.session_state.ws_logs = st.session_state.ws_logs[-20:]

async def websocket_handler():
    \"\"\"Handle WebSocket connection\"\"\"
    uri = \"wss://stream.binance.com:9443/ws/!ticker@arr\"
    
    try:
        add_log(\"Connecting to Binance WebSocket...\")
        st.session_state.ws_status = \"Connecting\"
        
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
            add_log(\"Connected successfully!\")
            st.session_state.ws_connected = True
            st.session_state.ws_status = \"Connected\"
            
            while not st.session_state.stop_websocket:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if isinstance(data, list):
                        # Filter USDT pairs
                        usdt_data = [item for item in data if item.get('s', '').endswith('USDT')]
                        
                        # Process data with volume
                        processed_data = []
                        for pair in usdt_data[:15]:  # Show more pairs
                            try:
                                symbol = pair['s']
                                current = float(pair['c'])
                                high = float(pair['h'])
                                low = float(pair['l'])
                                volume = float(pair['v'])  # 24h volume
                                
                                if low > 0:
                                    # Calculate metrics
                                    ld = ((current - low) / low) * 100
                                    hd = ((current - high) / high) * 100
                                    profit_margin = ((high - low) / low) * 100
                                    
                                    processed_data.append({
                                        'Symbol': symbol,
                                        'LD': f\"{ld:.2f}%\",
                                        'HD': f\"{hd:.2f}%\",
                                        '% Profit': f\"{profit_margin:.2f}%\",
                                        'Vol': f\"{volume:,.0f}\"
                                    })
                            except (ValueError, KeyError):
                                continue
                        
                        st.session_state.ws_data = processed_data
                        add_log(f\"Updated {len(processed_data)} USDT pairs with volume data\")
                        
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    add_log(\"Connection closed\")
                    break
                    
    except Exception as e:
        add_log(f\"Error: {str(e)}\")
    finally:
        st.session_state.ws_connected = False
        st.session_state.ws_status = \"Disconnected\"

def start_websocket():
    \"\"\"Start WebSocket connection\"\"\"
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

def stop_websocket():
    \"\"\"Stop WebSocket connection\"\"\"
    st.session_state.stop_websocket = True
    st.session_state.ws_connected = False
    st.session_state.ws_status = \"Disconnected\"

# Main UI
st.title(\"Binance USDT Tracker\")
st.markdown(\"Real-time USDT pair analysis\")

# Controls
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button(\"Start\", disabled=st.session_state.ws_connected):
        start_websocket()

with col2:
    if st.button(\"Stop\", disabled=not st.session_state.ws_connected):
        stop_websocket()

with col3:
    if st.session_state.ws_status == \"Connected\":
        st.success(f\"Status: {st.session_state.ws_status}\")
    elif st.session_state.ws_status == \"Connecting\":
        st.warning(f\"Status: {st.session_state.ws_status}\")
    else:
        st.info(f\"Status: {st.session_state.ws_status}\")

# Data display with volume
if st.session_state.ws_data:
    st.subheader(\"Live USDT Pairs (with Volume)\")
    df = pd.DataFrame(st.session_state.ws_data)
    st.dataframe(df, use_container_width=True)
    
    st.info(f\"Displaying {len(st.session_state.ws_data)} pairs - Volume column included\")

# Connection logs
if 'ws_logs' in st.session_state and st.session_state.ws_logs:
    with st.expander(\"Connection Log\"):
        for log_entry in st.session_state.ws_logs[-8:]:
            st.text(log_entry)

# Auto-refresh
if st.session_state.ws_connected:
    st.rerun()
