# backend.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import textwrap
from newsapi import NewsApiClient
from datetime import datetime

app = FastAPI(
    title="LARS AI Assistant Backend",
    description="Generates detailed intelligence reports for a domain and role using local LLaMA 3",
    version="1.0"
)

# CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "llama3"  # your local Ollama model name

# ----------------- Helper Functions -----------------

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

# ----------------- FastAPI Endpoints -----------------

@app.get("/")
async def root():
    return {"message": "LARS AI Assistant Backend is running!"}

@app.post("/generate")
async def generate(request: Request):
    """
    Receives JSON input:
    {
        "domain": "Marketing",
        "role": "Data Analyst"
    }
    Returns a detailed intelligence report.
    """
    try:
        data = await request.json()
        domain = data.get("domain", "").strip()
        role = data.get("role", "").strip()

        if not domain or not role:
            return {"error": "Please provide both 'domain' and 'role'."}

        safe_print(f"\n🧠 Generating report for domain='{domain}', role='{role}'...\n")
        
        # 1️⃣ Fetch recent trends
        recent_trends = fetch_recent_trends(domain, role)

        # 2️⃣ Build prompt for AI
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

        Make the answer factual, insightful, easy to read, and professional.
        Highlight AI tools clearly and explain their purpose in detail.
        """)

        # 3️⃣ Generate AI report
        report = generate_response_with_ollama(prompt)
        return {"output": report}

    except Exception as e:
        return {"error": f"Unexpected error: {e}"}
