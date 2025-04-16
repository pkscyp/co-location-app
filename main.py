import streamlit as st
import pandas as pd
import os 
import colocation as cl

st.set_page_config(
    page_title="Sentinel Offender Colocation",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.markdown("*Instruction to use application*")
st.markdown("***Use Splunk and run below query and export result as csv***")
st.markdown('''
    :orange[host=fjpdiotlsmo* PROCESSED-PAYLOAD gpstwap | spath input=payload| search "gpstwap.mth"=sa| rename IMEI as asset_id,gpstwap.gnss.lat as lat,gpstwap.gnss.lon as lon,gpstwap.ts as ts| table asset_id,ts,lat,lon|sort ts|where lat > 100000]
            
    Upload Downloaded File in this application.Select available or newly upload file and click run location
            
            ''')

listFiles = os.listdir("docdir")


(c1,c2) = st.columns(2)


uploaded_file = c2.file_uploader("Upload File",type=['.csv'])

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    name = uploaded_file.name
    with open(f"docdir/{name}", "wb") as binary_file:
        binary_file.write(bytes_data)
        st.success("Upload Successful..")
        listFiles = os.listdir("docdir")
        
fileToProcess = c1.selectbox(label='Select File',options=listFiles)
if fileToProcess:
    st.session_state.selected_file = fileToProcess


if c1.button('Run Colocation'):
    # st.success(' Loading colocation ')
    # st.write('loading file ',st.session_state.selected_file)
    cl.handleFile(c1,st.session_state.selected_file)

