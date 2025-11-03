# backend.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import textwrap
from newsapi import NewsApiClient
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time

app = FastAPI(
    title="LARS AI Assistant Backend",
    description="Generates detailed intelligence reports for a domain and role using local LLaMA 3 + weekly update system",
    version="2.0"
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "llama3"
SUBSCRIPTIONS_FILE = "subscriptions.json"

# ---------------- Helper Functions ----------------

def safe_print(text):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(text)


def fetch_recent_trends(domain, role, num_articles=5):
    """Fetch recent news/trends for the given domain and role using NewsAPI"""
    query = f"{domain} {role}"
    newsapi = NewsApiClient(api_key="9d1bc1332a514422b3eed3eefbd9d5c2")
    
    try:
        articles_data = newsapi.get_everything(
            q=query,
            language="en",
            sort_by="publishedAt",
            page_size=num_articles
        ).get('articles', [])

        insights = []
        current_time = datetime.now().strftime("%B %Y")
        insights.append(f"Insights as of {current_time}:\n")

        if articles_data:
            for article in articles_data:
                title = article.get("title", "")
                source = article.get("source", {}).get("name", "")
                published_at = article.get("publishedAt", "")
                published_month_year = datetime.strptime(published_at[:10], "%Y-%m-%d").strftime("%B %Y")
                title_lower = title.lower()
                if any(k in title_lower for k in ["study", "research", "paper", "report"]):
                    insights.append(f"A study published in {source} in {published_month_year} demonstrated: {title}.")
                elif any(k in title_lower for k in ["launch", "released", "introduced", "approved"]):
                    insights.append(f"In {published_month_year}, {source} launched: {title}, impacting {domain}/{role}.")
                elif any(k in title_lower for k in ["trending", "viral", "popular", "#"]):
                    insights.append(f"Trending on social media: {title} is gaining attention among {domain}/{role}.")
                elif any(k in title_lower for k in ["conference", "webinar", "workshop", "summit", "event"]):
                    insights.append(f"Upcoming in {published_month_year}: {title}, relevant to {role}/{domain}.")
                else:
                    insights.append(f"{title} ({source}, {published_month_year})")
            return "\n- " + "\n- ".join(insights)
        else:
            return "No recent news found."
    except Exception as e:
        return f"Error fetching trends: {e}"

def generate_response_with_ollama(prompt, model=MODEL_NAME, timeout=180):
    """Run Ollama locally to generate AI response"""
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )
        if result.returncode != 0:
            err = result.stderr.strip()
            if err:
                safe_print(f"\n⚠️ Model returned an error:\n{err}")
            return ""
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "⚠️ Timeout reached — model took too long to respond."
    except FileNotFoundError:
        return "❌ Error: 'ollama' not found. Make sure Ollama is installed and running."
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"


# ✅ Updated Email Function with Retry and Logging
def send_email(to_email, subject, html_content):
    """Send email via Gmail SMTP with retry and clear logs"""
    sender_email = "storagaeworkflow@gmail.com"
    sender_password = "uifh hlye iyvy csig"  # replace with valid Gmail App Password

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html"))

    for attempt in range(2):  # try twice
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, to_email, msg.as_string())
            safe_print(f"✅ Email sent successfully to {to_email}")
            return True
        except Exception as e:
            safe_print(f"❌ Attempt {attempt+1} failed to send email to {to_email}: {e}")
            time.sleep(3)
    return False


def send_weekly_updates():
    """Reads subscriptions.json and sends weekly updates to all users"""
    safe_print("\n📅 Running weekly email scheduler...")

    if not os.path.exists(SUBSCRIPTIONS_FILE):
        safe_print("⚠️ No subscriptions found.")
        return

    try:
        with open(SUBSCRIPTIONS_FILE, "r") as f:
            subs = json.load(f)

        if not subs:
            safe_print("⚠️ Subscription list is empty.")
            return

        for sub in subs:
            email = sub.get("email")
            domain = sub.get("domain")
            role = sub.get("role")

            if not email or not domain or not role:
                continue

            safe_print(f"📨 Generating weekly report for {email} ({domain} / {role})")

            # Generate weekly report
            recent_trends = fetch_recent_trends(domain, role)
            prompt = textwrap.dedent(f"""
            Generate a concise weekly intelligence update for a {role} in the {domain} domain.
            Include:
            - Key trends this week ({recent_trends})
            - New tools or frameworks
            - Notable AI or automation use cases
            - Skills or courses worth learning
            """)
            report = generate_response_with_ollama(prompt)

            # Compose email
            html_content = f"""
            <h2>Your Weekly LARS AI Update 🌐</h2>
            <p>Here’s your latest {domain} / {role} update:</p>
            <pre style="background:#f9f9f9;padding:12px;border-radius:8px;white-space:pre-wrap;">
            {report}
            </pre>
            <p>Stay smart, stay ahead — LARS AI 🚀</p>
            """
            send_email(email, f"Weekly {domain} / {role} Intelligence Update", html_content)

    except Exception as e:
        safe_print(f"❌ Weekly update scheduler error: {e}")


# ✅ Initialize scheduler to run once per week
scheduler = BackgroundScheduler()
scheduler.add_job(send_weekly_updates, "interval", weeks=1)
scheduler.start()
safe_print("✅ Weekly scheduler started (runs every 7 days).")

# Ensure graceful shutdown
atexit.register(lambda: scheduler.shutdown(wait=False))

# ---------------- Endpoints ----------------

@app.get("/")
async def root():
    return {"message": "LARS AI Assistant Backend is running!"}

@app.post("/generate")
async def generate(request: Request):
    """Generate domain-role intelligence report"""
    try:
        data = await request.json()
        domain = data.get("domain", "").strip()
        role = data.get("role", "").strip()

        if not domain or not role:
            return {"error": "Please provide both 'domain' and 'role'."}

        safe_print(f"\n🧠 Generating report for domain='{domain}', role='{role}'...\n")

        recent_trends = fetch_recent_trends(domain, role)

        prompt = textwrap.dedent(f"""
        You are a professional AI assistant. Generate a detailed, structured, and actionable intelligence report
        for a professional who works as a **{role}** in the **{domain}** domain.

        Include the following sections exactly as listed:

        1. Current Trends and Updates
           - Incorporate these recent trends from the web:
           {recent_trends}
           - Emerging technologies, tools, or methods affecting the domain.
           - Shifts in customer behavior, regulations, or market trends.

        2. Role-Relevant Practices / Tools
           - Methods, frameworks, or workflows that improve productivity.
           - Software, platforms, or tools commonly adopted in the field.

        3. AI & Automation Opportunities
           - Explain how AI or automation is being used to improve efficiency.
           - For every AI tool mentioned, provide:
             - Name of the tool
             - Detailed explanation of its function and purpose
             - A link where the user can try or explore the tool

        4. Skills & Learning Paths
           - Core skills everyone in this domain should know.
           - Emerging skills that give an edge.
           - Suggested learning resources (courses, articles, tutorials).

        5. Future Outlook
           - Trends that are likely to shape the domain in the next 1–5 years.
           - Opportunities and challenges to watch out for.

        6. Actionable Insights
           - Concrete steps the user can take to stay ahead (learning, networking, experimenting).
        """)

        report = generate_response_with_ollama(prompt)
        return {"output": report}

    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


# ✅ Updated Subscription Endpoint
@app.post("/subscribe")
async def subscribe(request: Request):
    """
    Example input:
    {
        "email": "user@example.com",
        "phone": "9876543210",  # optional
        "domain": "Marketing",
        "role": "Data Analyst"
    }
    """
    try:
        data = await request.json()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        domain = data.get("domain", "").strip()
        role = data.get("role", "").strip()

        if not email and not phone:
            return {"error": "Please provide at least an email or phone number."}

        # Save subscription locally
        subs = []
        if os.path.exists(SUBSCRIPTIONS_FILE):
            with open(SUBSCRIPTIONS_FILE, "r") as f:
                subs = json.load(f)

        new_sub = {"email": email, "phone": phone, "domain": domain, "role": role}
        subs.append(new_sub)

        with open(SUBSCRIPTIONS_FILE, "w") as f:
            json.dump(subs, f, indent=4)

        if email:
            weekly_link = f"http://localhost:8501//weekly-updates?domain={domain}&role={role}"
            html_content = f"""
            <h3>You're now subscribed to weekly updates 🎯</h3>
            <p>Every week, you’ll receive a fresh report for:</p>
            <b>Domain:</b> {domain}<br>
            <b>Role:</b> {role}<br><br>
            <a href="{weekly_link}" style="color:white;background:#007bff;padding:10px 20px;text-decoration:none;border-radius:6px;">
                View Weekly Report
            </a>
            <br><br>
            <p>Stay ahead with LARS AI 🚀</p>
            """

            success = send_email(email, "You're subscribed to weekly LARS AI updates!", html_content)
            if success:
                return {"message": f"✅ Subscription successful! Confirmation email sent to {email}"}
            else:
                return {"message": "⚠️ Subscription saved, but failed to send email (check logs)."}

        return {"message": "✅ Subscription successful! (no email provided)"}

    except Exception as e:
        safe_print(f"❌ Subscription error: {e}")
        return {"error": f"Subscription failed: {e}"}
