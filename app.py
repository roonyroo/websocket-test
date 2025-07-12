import streamlit as st
import os

# Page config
st.set_page_config(
    page_title=\"Railway Test\",
    page_icon=\"🚂\",
    layout=\"wide\"
)

st.title(\"Railway Deployment Test\")
st.success(\"✅ App is running on Railway!\")

# Show environment info
st.subheader(\"Environment Info\")
st.write(f\"PORT: {os.getenv('PORT', 'Not set')}\")
st.write(f\"Python version: {os.sys.version}\")

# Test WebSocket import
try:
    import websockets
    st.success(\"✅ WebSocket library imported successfully\")
except ImportError as e:
    st.error(f\"❌ WebSocket import failed: {e}\")

# Test pandas import
try:
    import pandas as pd
    st.success(\"✅ Pandas library imported successfully\")
except ImportError as e:
    st.error(f\"❌ Pandas import failed: {e}\")

st.markdown(\"---\")
st.markdown(\"If you see this page, Railway deployment is working!\")
