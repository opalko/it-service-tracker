import streamlit as st
from supabase import create_client, Client
import datetime
import traceback 

# Replace with your secret password
PASSWORD = "3bigdogsR0kforN0w"

def autocomplete_field(label, field_name):
    result = supabase.table("service_calls").select(field_name).execute()
    entries = sorted({row[field_name] for row in result.data if row.get(field_name)})

    key_base = label.lower().replace(" ", "_")
    selectbox_key = f"{key_base}_selectbox"
    textinput_key = f"{key_base}_input"

    options = ["Select one..."] + entries + [f"<Add new {label.lower()}>"]
    selected = st.selectbox(label, options=options, key=selectbox_key)

    # Always show the text input, even if unused
    new_value = st.text_input(f"Enter new {label.lower()}", key=textinput_key)

    # Return the proper value
    if selected == f"<Add new {label.lower()}>":
        return new_value
    elif selected == "Select one...":
        return ""
    else:
        return selected

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
        client = autocomplete_field("Client", "client")
        department = autocomplete_field("Department", "department")
        call_type = autocomplete_field("Call Type", "call_type")
        status = autocomplete_field("Status", "status")

            
        service_tag = st.text_input("Service Tag")
 #
    with col2:
        issue = st.text_area("Issue")
        resolution = st.text_area("Resolution")
        closed_on = st.date_input("Closed On", disabled=(status != "Closed"))
        notes = st.text_area("Notes")

    submitted = st.form_submit_button("Submit")

    if submitted:
        data = {
            "open_date": open_date.isoformat(),
            "client": client,
            "department": department,
            "service_tag": service_tag or "",
            "call_type": call_type,
            "issue": issue or "",
            "resolution": resolution or "",
            "status": status,
            "notes": notes or "",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        # Basic validation
        missing_fields = []
        if not client:
            missing_fields.append("Client")
        if not call_type:
            missing_fields.append("Call Type")
        if not status:
            missing_fields.append("Status")
        if not issue:
            missing_fields.append("Issue")

        if missing_fields:
            st.error(f"Please fill in the following required fields: {', '.join(missing_fields)}")
        else:
            data = {
                "open_date": open_date.isoformat(),
                "client": client,
                "department": department or "",
                "service_tag": service_tag or "",  # Required
                "call_type": call_type,
                "issue": issue or "",
                "resolution": resolution or "",    # Required
                "status": status or "",
                "notes": notes or "",              # Required
                "created_at": datetime.datetime.utcnow().isoformat() + "Z"
            }
            
            if status == "Closed":
                data["closed_on"] = closed_on.isoformat()
        
            # Remove created_at if it somehow snuck in
            data = {k: v for k, v in data.items() if v not in [None, ""]}

            if "created_at" in data:
                st.warning(f"created_at is present: {repr(data['created_at'])}")
            else:
                st.success("created_at is NOT in the data — default should apply")
 
            data["created_at"] = datetime.datetime.utcnow().isoformat() + "Z"

            st.subheader("✅ Final field types to Supabase")
            for k, v in data.items():
                st.write(f"{k}: type={type(v).__name__}, value={repr(v)}")

            try:
                result = supabase.table("service_calls").insert(data).execute()
                st.success("Call logged successfully!")
            except Exception as e:
                st.error("Insert failed:")
                st.text("Exception type: " + type(e).__name__)
                st.text("Exception message: " + str(e))
                st.text("Traceback:")
                st.text(traceback.format_exc())

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
