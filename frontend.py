import streamlit as st
import requests
import streamlit.components.v1 as components

# --- Page setup ---
st.set_page_config(
    page_title="LARS AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
body, .stApp {
    background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
    color: #f5f5f5;
    font-family: 'Segoe UI', sans-serif;
}
h1 {
    background: linear-gradient(90deg, #00ffd5, #00bba3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    text-align: center;
    margin-bottom: 5px;
}
h2,h3 {
    color: #00ffd5;
}
.sidebar .sidebar-content {
    background-color: rgba(0,0,0,0.25);
    color: #f5f5f5;
    backdrop-filter: blur(12px);
}
.sidebar h2, .sidebar h3 {
    color: #00ffd5;
}
.card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    padding: 25px;
    border-radius: 14px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    margin-bottom: 25px;
    transition: transform 0.3s, box-shadow 0.3s;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.8);
}
.stButton>button {
    background: linear-gradient(90deg, #00ffd5, #00bba3);
    color: #1c1c17;
    font-weight: bold;
    border-radius: 10px;
    padding: 10px 25px;
    font-size: 16px;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #00bba3, #00ffd5);
    color: white;
    transform: scale(1.05);
}
.feature {
    font-size: 24px;
    color: #00ffd5;
    margin-right: 12px;
    vertical-align: middle;
}
hr {
    border: none;
    height: 2px;
    background: linear-gradient(to right, transparent, rgba(255,255,255,0.4), transparent);
    margin: 2em 0;
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## LARS AI Assistant")
    st.markdown("Your AI-powered intelligence companion for any domain and role.")
    st.markdown("---")
    st.markdown("### Contact Info")
    st.markdown("📧 **Email:** support@larsai.com")
    st.markdown("📞 **Phone:** +91 9876543210")
    st.markdown("🌐 **Website:** [larsai.com](https://larsai.com)")
    st.markdown("---")
    st.markdown("### Quick Links")
    st.markdown("- Home\n- About Us\n- Try Domain Assistant\n- Features\n- Contact")

# --- Hero Section ---
st.markdown("<h1>Welcome to LARS AI Assistant 🤖</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:20px; color:#ccc;'>Your AI companion that generates <b>personalized intelligence reports</b> for your industry and role. Stay ahead of trends, make smarter decisions, and leverage insights tailored just for you.</p>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- About Section ---
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### About LARS AI Assistant")
st.markdown("""
LARS AI Assistant is a next-generation intelligence system built to empower professionals, 
entrepreneurs, and researchers.  
It generates **real-time insights** and comprehensive reports customized to your domain and role.  

Our assistant analyzes market trends, summarizes complex information, and provides strategic guidance — 
making LARS your trusted AI partner in achieving clarity, innovation, and growth.
""")
st.markdown("</div>", unsafe_allow_html=True)

# --- Features ---
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### Key Features")
st.markdown("""
<p><span class='feature'>💡</span> Real-time trend analysis</p>
<p><span class='feature'>🧠</span> Personalized insights for your role</p>
<p><span class='feature'>🚀</span> Easy-to-use AI interface</p>
<p><span class='feature'>📊</span> Exportable professional reports</p>
<p><span class='feature'>⚡</span> Fast, reliable, and constantly improving</p>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- Initialize session_state ---
if "show_assistant" not in st.session_state:
    st.session_state.show_assistant = False
if "generated_report" not in st.session_state:
    st.session_state.generated_report = None

# --- Try Assistant Button ---
st.markdown("<div style='text-align:center; margin:30px 0;'>", unsafe_allow_html=True)
if st.button("🚀 Try Domain Assistant"):
    st.session_state.show_assistant = True
st.markdown("</div>", unsafe_allow_html=True)

# --- Assistant Form ---
if st.session_state.show_assistant:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Generate Your Domain Intelligence Report")

    API_URL = "https://lars-ai-backend-7.onrender.com"

    with st.form("assistant_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Email Address")
        number = st.text_input("Phone Number")
        domain = st.text_input("Domain / Industry")
        role = st.text_input("Your Role in this Domain")
        submitted = st.form_submit_button("Generate Report")

    if submitted:
        if not domain.strip() or not role.strip():
            st.warning("⚠️ Please enter both your domain and role.")
        else:
            with st.spinner("Generating your intelligence report..."):
                try:
                    payload = {"name": name, "email": email, "number": number, "domain": domain, "role": role}
                    response = requests.post(f"{API_URL}/generate", json=payload)
                    data = response.json()
                    st.session_state.generated_report = data.get("output", data.get("error", "No response"))
                except Exception as e:
                    st.session_state.generated_report = f"Error contacting backend: {e}"
    st.markdown("</div>", unsafe_allow_html=True)

# --- Display Generated Report ---
if st.session_state.generated_report:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📄 Generated Intelligence Report")
    st.markdown(f"<p style='white-space: pre-wrap; font-size:16px; color:#eaeaea;'>{st.session_state.generated_report}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ✅ Browser push notification for generated report
    report_link = "#generated_report_section"  # optional anchor
    js_code = f"""
    <script>
    if (Notification.permission !== 'granted')
        Notification.requestPermission();
    else {{
        new Notification('LARS AI Update', {{
            body: 'Your domain intelligence report is ready! Click to view.',
            icon: 'https://larsai.com/favicon.ico'
        }}).onclick = function() {{
            window.focus();
            window.location.href = '{report_link}';
        }};
    }}
    </script>
    """
    components.html(js_code, height=0)

# --- Weekly Subscription Section ---
st.markdown("<div style='text-align:center; margin-top:20px;'>", unsafe_allow_html=True)
st.markdown("#### Want weekly insights delivered to your inbox? 📬")
if st.button("✨ Stay Updated Weekly"):
    if not (name.strip() and email.strip() and number.strip() and domain.strip() and role.strip()):
        st.warning("⚠️ Please fill in your Name, Email, Phone, Domain, and Role above before subscribing.")
    else:
        try:
            payload = {"name": name, "email": email, "number": number, "domain": domain, "role": role}
            response = requests.post(f"{API_URL}/subscribe", json=payload)
            data = response.json()
            if response.status_code == 200:
                st.success(f"🎉 {data.get('message', 'You are now subscribed for weekly updates!')} 🎆")
                st.balloons()

                # ✅ Browser push notification for subscription success
                js_code_sub = f"""
                <script>
                if (Notification.permission !== 'granted')
                    Notification.requestPermission();
                else {{
                    new Notification('LARS AI Weekly Updates', {{
                        body: 'You are successfully subscribed for weekly insights!',
                        icon: 'https://larsai.com/favicon.ico'
                    }});
                }}
                </script>
                """
                components.html(js_code_sub, height=0)
            else:
                st.error(f"⚠️ Subscription failed: {data.get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"⚠️ Error contacting backend: {e}")
st.markdown("</div>", unsafe_allow_html=True)