import os
import sys
import json
import re
import time
import gspread
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("✗ Error: GROQ_API_KEY is missing from .env!")
    sys.exit(1)

def sanitize_slug(name: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip().lower()
    return re.sub(r'[\s_]+', "-", clean)

def connect_to_sheet():
    for attempt in range(1, 4):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open("DSA_Instagram_Automation")
            worksheet = sh.worksheet("Tech_Bytes")
            return worksheet
        except Exception as e:
            print(f"⚠ Attempt {attempt}/3 connecting to Google Sheet failed: {e}")
            time.sleep(3)
    sys.exit("✗ Could not connect to Google Sheet tab 'Tech_Bytes'.")

def generate_tech_byte(category: str, topic_name: str, keywords: str) -> dict:
    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
You are a Principal Software Engineer and master technical educator.
Produce an exhaustive, highly engaging deep-dive guide on:
- Topic: {topic_name}
- Category: {category}
- Focus Keywords: {keywords}

Output MUST be a single valid raw JSON object strictly matching this schema:
{{
  "tldr": "One punchy sentence summarizing the core distinction/essence.",
  "eli5": "Explain Like I'm 5: A fun, intuitive, vivid real-world analogy (2-3 paragraphs) without technical jargon.",
  "deep_dive": "Exhaustive engineering breakdown explaining how it works under the hood at the OS, protocol, or byte level.",
  "comparison_table": "Markdown table comparing key parameters (Features, Performance, Overhead, Best For).",
  "mermaid_diagram": "Valid Mermaid.js graph code (starting with graph TD or graph LR) illustrating the workflow or structure.",
  "real_world_cases": "3 specific, concrete production scenarios explaining when to use which option.",
  "misconceptions": "2-3 popular developer myths or historical trivia about this topic.",
  "reference_links": "Markdown list of 3-4 authoritative reference links, RFCs, or official documentation."
}}
"""
    candidate_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]

    for model_name in candidate_models:
        try:
            print(f"🤖 Generating with model: {model_name}...")
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized technical documentation engine. Output only a valid raw JSON object. Do not wrap output in markdown fences."
                    },
                    {"role": "user", "content": prompt}
                ],
                model=model_name,
                response_format={"type": "json_object"},
                max_tokens=6000,
                temperature=0.2
            )
            raw_text = response.choices[0].message.content

            if "<think>" in raw_text and "</think>" in raw_text:
                think_end = raw_text.find("</think>")
                raw_text = raw_text[think_end + len("</think>"):].strip()

            start_idx = raw_text.find("{")
            end_idx = raw_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                return json.loads(raw_text[start_idx:end_idx+1])
        except Exception as err:
            print(f"⚠ Model {model_name} failed: {err}. Trying next fallback...")

    sys.exit("✗ All candidate models failed to generate content.")

def clean_formatting(text: str) -> str:
    if not isinstance(text, str):
        return ""
    if "\\n" in text:
        text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "    ")
    return text.strip()

def assemble_markdown(topic: str, category: str, data: dict) -> str:
    fence = "```"
    mermaid_content = clean_formatting(data.get("mermaid_diagram", ""))
    mermaid_block = f"{fence}mermaid\n{mermaid_content}\n{fence}"

    sections = [
        f"# 💡 {topic}",
        f"> **TL;DR:** {clean_formatting(data.get('tldr', ''))}",
        "---",
        "## 👶 Explain Like I'm 5 (ELI5)",
        clean_formatting(data.get("eli5", "")),
        "---",
        "## 🔍 The Technical Deep-Dive",
        clean_formatting(data.get("deep_dive", "")),
        "### 📊 Comparison Matrix",
        clean_formatting(data.get("comparison_table", "")),
        "---",
        "## 🗺️ Visual Architecture & Flow",
        mermaid_block,
        "---",
        "## 🛠️ Real-World Production Scenarios",
        clean_formatting(data.get("real_world_cases", "")),
        "---",
        "## ⚠️ Common Myths & Gotchas",
        clean_formatting(data.get("misconceptions", "")),
        "---",
        "## 🔗 Authoritative References & RFCs",
        clean_formatting(data.get("reference_links", ""))
    ]
    return "\n\n".join(sections) + "\n"

def update_root_readme(topic_id: str, category: str, topic: str, relative_path: str, tldr: str):
    root_readme = "README.md"
    entry = f"| #{topic_id} | `{category}` | [{topic}](./{relative_path}) | {tldr} | ✅ Done |\n"

    if not os.path.exists(root_readme) or os.stat(root_readme).st_size == 0:
        initial_content = (
            "# 🧠 Daily Bite-Sized Tech & CS Fundamentals\n\n"
            "An automated archive exploring computer science concepts, protocols, file formats, and systems design principles "
            "with ELI5 analogies, technical deep-dives, visual diagrams, and real-world production gotchas.\n\n"
            "| ID | Category | Concept / Question | Core Takeaway | Status |\n"
            "| :---: | :--- | :--- | :--- | :---: |\n"
        )
        with open(root_readme, "w", encoding="utf-8") as f:
            f.write(initial_content)

    with open(root_readme, "a", encoding="utf-8") as f:
        f.write(entry)

def main():
    print("📡 Connecting to Google Sheet 'DSA_Instagram_Automation' (Tab: 'Tech_Bytes')...")
    worksheet = connect_to_sheet()
    records = worksheet.get_all_records()
    headers = worksheet.row_values(1)

    if "Status" not in headers:
        sys.exit("✗ 'Status' column not found in Google Sheet. Please add it.")
    status_col_idx = headers.index("Status") + 1

    pending_rows = [(idx + 2, r) for idx, r in enumerate(records) if str(r.get("Status", "")).strip().lower() == "pending"]
    if not pending_rows:
        print("✓ All topics are completed! Add more pending rows in Google Sheets.")
        return

    row_num, row_data = pending_rows[0]
    topic_id = str(row_data.get("ID", row_num - 1))
    category = str(row_data.get("Category", "General")).strip()
    topic_name = str(row_data.get("Topic Name")).strip()
    keywords = str(row_data.get("Keywords", "")).strip()

    print(f"🎯 Processing #{topic_id} [{category}]: {topic_name}")

    data = generate_tech_byte(category, topic_name, keywords)

    cat_dir = sanitize_slug(category)
    topic_dir = sanitize_slug(topic_name)
    target_path = os.path.join("topics", cat_dir, topic_dir)
    os.makedirs(target_path, exist_ok=True)

    markdown_content = assemble_markdown(topic_name, category, data)
    file_path = os.path.join(target_path, "README.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"  └── Created: {file_path}")

    tldr_summary = clean_formatting(data.get("tldr", "")).replace("|", "-")
    update_root_readme(topic_id, category, topic_name, file_path, tldr_summary)
    print("✓ Root README.md index updated!")

    worksheet.update_cell(row_num, status_col_idx, "Completed")
    print(f"✓ Google Sheet row {row_num} marked as 'Completed'!")

if __name__ == "__main__":
    main()