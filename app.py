import streamlit as st
from supabase import create_client, Client
import datetime

# --- CONFIG ---
PASSWORD = "3bigdogsR0kforN0w"
SUPABASE_URL = "https://mlieytogymwftsurhrbg.supabase.co/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1saWV5dG9neW13ZnRzdXJocmJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxNDU2NTAsImV4cCI6MjA2NDcyMTY1MH0.BtXRDlTxDSFgtXTeTclawD45R4ydj0juF0pF19LKxNw"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
st.set_page_config(page_title="IT Service Call Tracker", layout="wide")
st.title("📞 IT Service Call Tracker")

# --- AUTH ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pwd = st.text_input("Enter password:", type="password")
    if st.button("Login") and pwd == PASSWORD:
        st.session_state.authenticated = True
    elif pwd and pwd != PASSWORD:
        st.error("Wrong password")
    st.stop()

# --- AUTOCOMPLETE FIELD ---
def autocomplete_field(label, field_name):
    result = supabase.table("service_calls").select(field_name).execute()
    entries = sorted({row[field_name] for row in result.data if row.get(field_name)})
    key_base = label.lower().replace(" ", "_")
    selected = st.selectbox(label, ["Select one..."] + entries + [f"<Add new {label.lower()}>"], key=f"{key_base}_selectbox")
    new_value = st.text_input(f"Enter new {label.lower()}", key=f"{key_base}_input")
    if selected == f"<Add new {label.lower()}>":
        return new_value.strip()
    elif selected == "Select one...":
        return ""
    else:
        return selected.strip()

# --- FORM ---
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
    with col2:
        issue = st.text_area("Issue")
        resolution = st.text_area("Resolution")
        closed_on = st.date_input("Closed On", disabled=(status != "Closed"))
        notes = st.text_area("Notes")

    submitted = st.form_submit_button("Submit")

    if submitted:
        required_fields = {
            "Client": client,
            "Call Type": call_type,
            "Status": status,
            "Issue": issue,
        }
        missing = [label for label, value in required_fields.items() if not value.strip()]

        if missing:
            st.error(f"Please complete: {', '.join(missing)}")
        else:
            data = {
                "open_date": open_date.isoformat(),
                "client": client,
                "department": department or "",
                "service_tag": service_tag or "",
                "call_type": call_type,
                "issue": issue or "",
                "resolution": resolution or "",
                "status": status,
                "notes": notes or "",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
            if status == "Closed":
                data["closed_on"] = closed_on.isoformat()

            try:
                supabase.table("service_calls").insert(data).execute()
                st.success("Call logged successfully!")
            except Exception as e:
                st.error("Insert failed.")
                st.text(str(e))

# --- DISPLAY DATA ---
st.write("### 📋 Existing Calls")
try:
    calls = supabase.table("service_calls").select("*").order("open_date", desc=True).execute()
    if calls.data:
        st.dataframe(calls.data, use_container_width=True)
    else:
        st.warning("No calls found in the database.")
except Exception as e:
    st.error(f"Failed to load data: {e}")

st.subheader("📝 Edit Existing Call")

# Fetch all calls
calls = supabase.table("service_calls").select("*").order("open_date", desc=True).execute()

if calls.data:
    # Create a dropdown to select a call by client/issue/ID
    call_options = {f"{row['client']} – {row['issue']}": row for row in calls.data}
    selected_label = st.selectbox("Select a call to edit", list(call_options.keys()))
    selected_call = call_options[selected_label]

    with st.form("edit_call_form"):
        st.write(f"Editing call ID: {selected_call['id']}")

        new_status = st.selectbox("Status", ["Open", "In Progress", "Closed"], index=["Open", "In Progress", "Closed"].index(selected_call["status"]))
        new_resolution = st.text_area("Resolution", value=selected_call.get("resolution", ""))
        new_notes = st.text_area("Notes", value=selected_call.get("notes", ""))
        new_closed_on = st.date_input("Closed On", value=datetime.date.today() if not selected_call.get("closed_on") else datetime.date.fromisoformat(selected_call["closed_on"]), disabled=(new_status != "Closed"))

        submitted = st.form_submit_button("Save Changes")

        if submitted:
            update_data = {
                "status": new_status,
                "resolution": new_resolution,
                "notes": new_notes,
                "closed_on": new_closed_on.isoformat() if new_status == "Closed" else None,
            }

            try:
                supabase.table("service_calls").update(update_data).eq("id", selected_call["id"]).execute()
                st.success("Call updated successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error("Failed to update call.")
                st.text(str(e))
else:
    st.info("No calls available to edit.")
