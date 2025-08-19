# strategy.py
import os, json, re
from datetime import date, timedelta
from openai import OpenAI

# ✅ Create client explicitly with API key
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None


def extract_json_from_text(s: str):
    """Robustly extract first JSON object from text"""
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in response")

    json_str = s[start:end+1]
    json_str = json_str.replace("\n", " ")

    try:
        return json.loads(json_str)
    except Exception:
        # fallback: fix single quotes
        json_str2 = re.sub(r"(?<!\\)'", '"', json_str)
        return json.loads(json_str2)


def generate_strategy_with_openai(topic, audience="Gen Z", goal="engagement"):
    """
    Calls OpenAI GPT and requests a strict JSON response:
    {
      "subtopics": [...],
      "formats": [{"name":"", "reason":""}, ...],
      "calendar": [{"day":1,"title":"", "format":"", "notes":""}, ...]  # 30 entries
    }
    """
    if not client:
        raise EnvironmentError("❌ OPENAI_API_KEY not set in environment")

    system = {
        "role": "system",
        "content": (
            "You are an expert content strategist. "
            "Respond ONLY with a single JSON object with keys: "
            "subtopics (list of strings), "
            "formats (list of objects with 'name' and 'reason'), and "
            "calendar (list of exactly 30 objects with keys day,title,format,notes). "
            "No extra commentary."
        )
    }

    user = {
        "role": "user",
        "content": (
            f"Topic: {topic}\nAudience: {audience}\nGoal: {goal}\n"
            "Return a JSON exactly as described."
        )
    }

    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # ✅ modern lightweight model
        messages=[system, user],
        temperature=0.7,
        max_tokens=1000
    )

    text = resp.choices[0].message.content

    try:
        data = extract_json_from_text(text)

        # Minimal validation
        if "calendar" not in data or len(data.get("calendar", [])) < 30:
            data["calendar"] = auto_generate_calendar(
                data.get("subtopics", []),
                data.get("formats", [])
            )
        return data

    except Exception:
        # fallback to basic generator
        return auto_generate_fallback(topic, audience, goal)


def auto_generate_calendar(subtopics, formats):
    subtopics = subtopics or ["Key Tip 1", "Key Tip 2", "How-to", "Case Study"]
    formats = [f.get("name") if isinstance(f, dict) else str(f)
               for f in (formats or ["Reel", "Short", "Carousel"])]

    cal = []
    for i in range(30):
        day = i + 1
        st = subtopics[i % len(subtopics)]
        fmt = formats[i % len(formats)]
        title = f"{st} — Short {day}"
        cal.append({
            "day": day,
            "title": title,
            "format": fmt,
            "notes": ""
        })
    return cal


def auto_generate_fallback(topic, audience, goal):
    subtopics = [f"{topic} Quick Tip #{i+1}" for i in range(4)]
    formats = [
        {"name": "Instagram Reel", "reason": "High engagement short video"},
        {"name": "YouTube Short", "reason": "Good for discovery"},
        {"name": "Carousel", "reason": "Saves educational content"}
    ]
    calendar = auto_generate_calendar(subtopics, formats)
    return {"subtopics": subtopics, "formats": formats, "calendar": calendar}
