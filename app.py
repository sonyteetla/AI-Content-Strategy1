# app.py
import streamlit as st
import pandas as pd
import json
from data_fetch import get_trend_or_mock
from strategy import generate_strategy_with_openai, auto_generate_fallback
from fpdf import FPDF
import os
import urllib.request
import zipfile
import altair as alt

st.set_page_config(page_title="Trendify AI — Content Strategy", layout="wide", page_icon="🚀")

# 🔹 Custom CSS for Professional Technical UI + Hover
st.markdown("""
<style>
/* Background */
.stApp {
    background: linear-gradient(rgba(173, 216, 230, 0.7), rgba(173, 216, 230, 0.7));
}

/* Header */
h1 {
    font-size: 2.5em;
    color: #0B3D91;
    text-align: center;
    margin-bottom: 20px;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.4);
}

/* Buttons */
.stButton>button {
    background-color: #0B3D91;
    color: white;
    font-size: 18px;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #063970;
}
.stDownloadButton>button {
    background-color: #007ACC;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}

/* DataFrames and Containers */
.stDataFrame, .stMarkdown, .stTextInput, .stSelectbox {
    background-color: rgba(255, 255, 255, 0.95) !important;
    color: #0B3D91 !important;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
}

/* Sidebar */
.sidebar .sidebar-content {
    background-color: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 12px;
}

/* Subtopic Cards + Hover Animation */
.subtopic-card {
    background-color: rgba(255, 255, 255, 0.9);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.15);
    transition: transform 0.2s, box-shadow 0.2s;
}
.subtopic-card:hover {
    transform: translateY(-5px);
    box-shadow: 4px 4px 12px rgba(0,0,0,0.25);
}
.subtopic-card h4 {
    color: #0B3D91;
    margin-bottom: 5px;
}
.subtopic-card p {
    margin:2px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown("<h1>🚀 Trendify AI — Content Strategy Engine</h1>", unsafe_allow_html=True)
st.write("Enter topic, audience and goal — click Generate. AI key enables advanced strategy.")

col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("Topic", value="Skincare")
    audience = st.selectbox("Target Audience", ["Gen Z", "Millennials", "Professionals"], index=0)
    goal = st.selectbox("Primary Goal", ["Engagement", "Awareness", "Sales"], index=0)
    generate = st.button("Generate Strategy")

with col2:
    st.image("assets/logo.png" if os.path.exists("assets/logo.png") else "https://via.placeholder.com/120", width=120)
    if os.getenv("OPENAI_API_KEY") or "OPENAI_API_KEY" in st.secrets:
        st.success("✅ OpenAI API Key loaded. AI generation enabled!")
    else:
        st.warning("⚠️ Running in fallback mode — Set OPENAI_API_KEY for full AI power.")

# ---------------- Generate Strategy ----------------
if generate:
    with st.spinner("Fetching trends and generating strategy..."):
        # Trend graph
        trend_res = get_trend_or_mock(topic.lower())
        series = trend_res["data"]
        st.subheader("📈 Trend Graph")

        df_trend = pd.DataFrame({"Day": list(range(1, len(series)+1)), "Value": series})
        chart = alt.Chart(df_trend).mark_line(point=True, color="#0B3D91").encode(
            x=alt.X("Day", title="Day"),
            y=alt.Y("Value", title="Trend Value"),
            tooltip=["Day", "Value"]
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

        # AI Strategy
        try:
            strategy = generate_strategy_with_openai(topic, audience, goal)
        except Exception:
            st.warning("OpenAI unavailable or API key not set — using fallback generator.")
            strategy = auto_generate_fallback(topic, audience, goal)

        # ---------------- AI Strategy Summary with Cards + Sample Descriptions ----------------
        st.subheader("🧠 AI Strategy Summary")
        st.markdown("**Top subtopics with descriptions & remedies:**")

        subtopics = strategy.get("subtopics", [])
        if subtopics and isinstance(subtopics[0], str):
            # Add sample description & remedy
            subtopics = [
                {"title": s,
                 "description": f"Sample description for '{s}' explaining key points.",
                 "remedy": f"Sample remedy/tip for '{s}' to maintain effectiveness."}
                for s in subtopics
            ]

        for idx, sub in enumerate(subtopics):
            st.markdown(f"""
            <div class="subtopic-card">
                <h4>{idx}: {sub.get('title')}</h4>
                <p><strong>Description:</strong> {sub.get('description')}</p>
                <p><strong>Remedy/Tip:</strong> {sub.get('remedy')}</p>
            </div>
            """, unsafe_allow_html=True)

        # ---------------- Recommended Formats ----------------
        st.markdown("**Recommended formats:**")
        for f in strategy.get("formats", []):
            if isinstance(f, dict):
                st.write(f"- **{f.get('name')}** — {f.get('reason')}")
            else:
                st.write(f"- {f}")

        # ---------------- 30-Day Content Calendar ----------------
        st.subheader("📅 30-Day Content Calendar")
        cal = strategy.get("calendar", [])
        df = pd.DataFrame(cal)
        st.dataframe(df)

        # ---------------- Downloads ----------------
        st.subheader("📥 Export")
        # JSON
        json_bytes = json.dumps(strategy, indent=2).encode("utf-8")
        st.download_button("Download strategy (JSON)", data=json_bytes, file_name=f"{topic}_strategy.json", mime="application/json")
        # CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download calendar (CSV)", data=csv_bytes, file_name=f"{topic}_calendar.csv", mime="text/csv")

        # ---------------- PDF Export ----------------
        pdf = FPDF()
        pdf.add_page()
        font_path = "DejaVuSans.ttf"
        if not os.path.exists(font_path):
            st.info("Downloading DejaVuSans font (first time)...")
            url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-sans-ttf-2.37.zip"
            zip_path = "dejavu.zip"
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for f in zip_ref.namelist():
                    if f.endswith("DejaVuSans.ttf"):
                        zip_ref.extract(f)
                        os.rename(f, font_path)
                        break

        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", "", 14)
        pdf.cell(0, 10, f"Content Strategy: {topic}", ln=True)
        pdf.ln(5)
        pdf.set_font("DejaVu", "", 12)
        for idx, sub in enumerate(subtopics):
            pdf.multi_cell(0, 7, f"{idx}: {sub.get('title')}")
            pdf.multi_cell(0, 6, f"Description: {sub.get('description')}")
            pdf.multi_cell(0, 6, f"Remedy/Tip: {sub.get('remedy')}")
            pdf.ln(3)

        pdf.multi_cell(0, 7, "\nRecommended Formats:")
        for f in strategy.get("formats", []):
            pdf.multi_cell(0, 6, f"- {(f.get('name') if isinstance(f, dict) else f)}: {(f.get('reason') if isinstance(f, dict) else '')}")

        pdf.multi_cell(0, 7, "\nCalendar (first 10 days):")
        for row in cal[:10]:
            pdf.multi_cell(0, 6, f"Day {row.get('day')}: {row.get('title')} ({row.get('format')})")

        pdf_bytes = pdf.output(dest="S").encode("latin-1", "ignore")
        st.download_button("Download PDF Summary", data=pdf_bytes, file_name=f"{topic}_summary.pdf", mime="application/pdf")
