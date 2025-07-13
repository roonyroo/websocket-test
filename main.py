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
    if len(st.session_state.ws_logs) > 15:
        st.session_state.ws_logs = st.session_state.ws_logs[-15:]

async def websocket_connection():
    \"\"\"Pure WebSocket connection - no REST fallback\"\"\"
    uri = \"wss://stream.binance.com:9443/ws/!ticker@arr\"
    
    add_log(\"Connecting to Binance WebSocket...\")
    st.session_state.ws_status = \"Connecting\"
    
    try:
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
            add_log(\"WebSocket connected successfully!\")
            st.session_state.ws_connected = True
            st.session_state.ws_status = \"Connected\"
            
            # Continuous WebSocket data stream
            while not st.session_state.stop_websocket:
                try:
                    # Receive WebSocket message
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    if isinstance(data, list):
                        # Filter USDT pairs only
                        usdt_pairs = [item for item in data if item.get('s', '').endswith('USDT')]
                        
                        # Process WebSocket data
                        processed_data = []
                        for pair in usdt_pairs[:20]:
                            try:
                                symbol = pair['s']
                                current = float(pair['c'])
                                high = float(pair['h'])
                                low = float(pair['l'])
                                volume = float(pair['v'])
                                
                                if low > 0:
                                    # Calculate profit metrics
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
                        
                        # Update session state with WebSocket data
                        st.session_state.ws_data = processed_data
                        add_log(f\"WebSocket updated {len(processed_data)} USDT pairs\")
                        
                except asyncio.TimeoutError:
                    # Timeout for stop signal checking
                    continue
                except websockets.exceptions.ConnectionClosed:
                    add_log(\"WebSocket connection closed\")
                    break
                except json.JSONDecodeError:
                    add_log(\"Invalid JSON received from WebSocket\")
                    continue
                    
    except websockets.exceptions.WebSocketException as e:
        add_log(f\"WebSocket error: {str(e)}\")
    except Exception as e:
        add_log(f\"Connection error: {str(e)}\")
    finally:
        st.session_state.ws_connected = False
        st.session_state.ws_status = \"Disconnected\"
        add_log(\"WebSocket connection terminated\")

def start_websocket():
    \"\"\"Start WebSocket connection in separate thread\"\"\"
    if not st.session_state.ws_connected and (st.session_state.ws_thread is None or not st.session_state.ws_thread.is_alive()):
        st.session_state.stop_websocket = False
        
        def websocket_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(websocket_connection())
            finally:
                loop.close()
        
        st.session_state.ws_thread = threading.Thread(target=websocket_thread, daemon=True)
        st.session_state.ws_thread.start()
        add_log(\"Starting WebSocket connection...\")

def stop_websocket():
    \"\"\"Stop WebSocket connection\"\"\"
    st.session_state.stop_websocket = True
    st.session_state.ws_connected = False
    st.session_state.ws_status = \"Disconnected\"
    add_log(\"Stopping WebSocket connection...\")

# Main UI
st.title(\"Binance USDT WebSocket Tracker\")
st.markdown(\"**Pure WebSocket streaming - no REST API calls**\")

# WebSocket controls
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button(\"Start WebSocket\", disabled=st.session_state.ws_connected):
        start_websocket()

with col2:
    if st.button(\"Stop WebSocket\", disabled=not st.session_state.ws_connected):
        stop_websocket()

with col3:
    if st.session_state.ws_status == \"Connected\":
        st.success(f\"WebSocket: {st.session_state.ws_status}\")
    elif st.session_state.ws_status == \"Connecting\":
        st.warning(f\"WebSocket: {st.session_state.ws_status}\")
    else:
        st.info(f\"WebSocket: {st.session_state.ws_status}\")

# WebSocket data display
if st.session_state.ws_data:
    st.subheader(\"Live WebSocket Data\")
    df = pd.DataFrame(st.session_state.ws_data)
    st.dataframe(df, use_container_width=True)
    
    st.info(f\"Streaming {len(st.session_state.ws_data)} USDT pairs via WebSocket\")
else:
    st.info(\"No WebSocket data - click 'Start WebSocket' to begin streaming\")

# WebSocket logs
if 'ws_logs' in st.session_state and st.session_state.ws_logs:
    with st.expander(\"WebSocket Connection Log\"):
        for log_entry in st.session_state.ws_logs:
            st.text(log_entry)

# Auto-refresh for WebSocket updates
if st.session_state.ws_connected:
    st.rerun()

st.markdown(\"---\")
st.markdown(\"*Pure WebSocket implementation - no REST API fallback*\")
