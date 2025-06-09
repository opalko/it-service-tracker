import streamlit as st
from supabase import create_client, Client
import datetime

# Replace with your secret password
PASSWORD = "3bigdogsR0kforN0w"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pwd = st.text_input("Enter password:", type="password")
    if st.button("Login") and pwd == PASSWORD:
        st.session_state.authenticated = True
    elif pwd and pwd != PASSWORD:
        st.error("Wrong password")
    st.stop()

# Replace with your Supabase details
SUPABASE_URL = "https://mlieytogymwftsurhrbg.supabase.co/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1saWV5dG9neW13ZnRzdXJocmJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxNDU2NTAsImV4cCI6MjA2NDcyMTY1MH0.BtXRDlTxDSFgtXTeTclawD45R4ydj0juF0pF19LKxNw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="IT Service Call Tracker", layout="wide")
st.title("📞 IT Service Call Tracker")

# --- FORM TO SUBMIT NEW CALL ---
with st.form("new_call_form", clear_on_submit=True):
    st.subheader("Log a New Call")
    col1, col2 = st.columns(2)
    with col1:
        open_date = st.date_input("Open Date", value=datetime.date.today())
        # Get all unique client names from existing data
        client_result = supabase.table("service_calls").select("client").execute()
        clients = sorted({row["client"] for row in client_result.data if row.get("client")})

        # Autocomplete-style field with fallback for new names
        client = st.selectbox("Client", options=clients + ["<Add new client>"])
        if client == "<Add new client>":
            client = st.text_input("Enter new client name")

        client = st.text_input("Client")
        department = st.text_input("Department")
        service_tag = st.text_input("Service Tag")
        call_type = st.selectbox("Call Type", ["Hardware", "Software", "Network", "Other"])
    with col2:
        issue = st.text_area("Issue")
        resolution = st.text_area("Resolution")
        status = st.selectbox("Status", ["Open", "In Progress", "Closed"])
        closed_on = st.date_input("Closed On", disabled=(status != "Closed"))
        notes = st.text_area("Notes")

    submitted = st.form_submit_button("Submit")

    if submitted:
        data = {
            "open_date": open_date.isoformat(),
            "client": client,
            "department": department,
            "service_tag": service_tag,
            "call_type": call_type,
            "issue": issue,
            "resolution": resolution,
            "status": status,
            "closed_on": closed_on.isoformat() if status == "Closed" else None,
            "notes": notes,
        }
        result = supabase.table("service_calls").insert(data).execute()
        if result.error:
            st.error("Failed to submit data.")
        else:
            st.success("Call logged successfully!")

# --- DISPLAY TABLE OF CALLS ---
st.write("### 📋 Existing Calls")

try:
    calls = supabase.table("service_calls").select("*").order("open_date", desc=True).execute()
    st.write("Raw data returned from Supabase:")
    if calls.data:
        st.dataframe(calls.data, use_container_width=True)
    else:
        st.warning("No calls found in the database.")
except Exception as e:
    st.error(f"Failed to load data: {e}")
