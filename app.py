import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Set up the Webpage
st.set_page_config(page_title="AC Machines Visualizer", layout="wide")
st.title("⚡ AC Machines Visual Exam Generator")
st.markdown("Upload your lab CSV data, and type **/visual_exam** to begin.")

# 2. Securely grab the API Key from Streamlit Vault
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("API Key missing! Please add it to the Streamlit Advanced Settings Secrets vault.")
    st.stop()

# 3. The System Instructions we built earlier
system_instruction = """
You are an Electrical Engineering exam writer. 
1. You generate calculation questions based ONLY on the provided CSV data.
2. Assume supply frequency is 50 Hz.
3. Deduce the number of poles from the highest no-load speed.
4. When the user types /visual_exam, use Python Code Execution to plot a relevant graph (e.g. Speed vs Torque or Efficiency) from the data, show it, and ask a question requiring the user to extract a value from the graph.
"""

# Configure the Gemini Model with Code Execution enabled
model = genai.GenerativeModel(
    model_name="gemini-1.5-latest",
    system_instruction=system_instruction,
    tools="code_execution" 
)

# 4. File Uploader for the CSVs
uploaded_file = st.file_uploader("Drop your Lab Data CSV here", type=["csv"])

if uploaded_file is not None:
    # Read the CSV so the AI can see it
    df = pd.read_csv(uploaded_file)
    csv_string = df.to_csv(index=False)
    st.success("Data loaded successfully! Type /visual_exam below.")
    
    # 5. Chat Interface
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

    user_input = st.chat_input("Ask a question or type /visual_exam")
    
    if user_input:
        # Display user message
        st.chat_message("user").write(user_input)
        
        # Combine the CSV data with the user's prompt so the AI has context
        full_prompt = f"Here is the lab data:\n{csv_string}\n\nUser request: {user_input}"
        
        # Get AI response
        with st.spinner("Generating..."):
            response = st.session_state.chat.send_message(full_prompt)
            st.chat_message("ai").write(response.text)
