# 🧠 Content Agent Project (n8n Workflow)

This project automates the **content creation, evaluation, and engagement analysis** process using **n8n**, **OpenAI**, and **Reddit API**.  
It streamlines how content is generated, scored, and tracked for performance — with automatic CSV reports and optional Discord notifications.

---

## 📘 Project Summary

The **Content Agent Workflow** combines two automation pipelines into one integrated system:

1. **Content Generation & Scoring**
   - Generates multiple creative content variants using OpenAI.
   - Evaluates each variant based on language quality and brand tone.
   - Filters approved and failed content automatically (no manual steps).
   - Generates image prompt suggestions for approved variants.

2. **Engagement Tracking & Analytics**
   - Fetches Reddit posts weekly using keywords or subreddits.
   - Calculates engagement (`upvotes + comments`) for each post.
   - Flags top-performing posts as **best content**.
   - Exports structured CSV reports for analytics and tracking.

---

## ⚙️ Main Features

| Feature | Description |
|----------|-------------|
| 🤖 AI Content Generation | Uses GPT models to produce marketing/ad content variants. |
| ✅ Quality Evaluation | Automatically scores and approves high-quality content. |
| 🖼️ Visual Concepts | Creates short image prompts for approved headlines. |
| 📊 Engagement Analytics | Fetches and ranks Reddit posts by engagement score. |
| 🧾 CSV Reporting | Exports results into downloadable CSV files. |
| 🔔 Discord Alerts | Sends workflow updates to a team channel. |
| 📅 Automation | Runs weekly on a schedule with no manual work required. |

---

## 🧩 Workflow Overview

```plaintext
Step 1 → Receive Brand Input / Prompt  
Step 2 → Generate Multiple Variants (OpenAI)  
Step 3 → Quality Check & Scoring Logic  
Step 4 → Filter Approved / Failed Variants  
Step 5 → Approved → Visual Concepts → CSV Export  
Step 6 → Failed → CSV Export for Manual Review  
Step 7 → Reddit Fetch → Compute Engagement  
Step 8 → Flag Best Content → Export Weekly CSV Reports  
Step 9 → Discord Webhook Notification
```

---

## 📦 Output Files

| File | Description |
|------|--------------|
| `approved_variants_<timestamp>.csv` | Approved AI-generated content variants |
| `failed_variants_<timestamp>.csv` | Rejected or low-quality variants |
| `flagged_post_stats_<timestamp>.csv` | Reddit posts with top engagement |
| `unflagged_post_stats_<timestamp>.csv` | All other tracked Reddit posts |

---

## 🔧 Tools & Technologies

- **n8n** – Workflow automation platform  
- **OpenAI API** – AI content generation  
- **Reddit API** – Fetching public post data  
- **Discord Webhook** – Sending alerts and summaries  
- **JavaScript Nodes** – Custom scoring and filtering logic  
- **CSV Export Nodes** – Data reporting and logs  

---

## 🚀 How to Use the Workflow

1. **Open n8n**  
   Start your local n8n instance or use the Desktop app.

2. **Import the Workflow**  
   - Click **Import from File**  
   - Select: `content_agent_full_workflow.json`

3. **Add Credentials**  
   - OpenAI API Key → for text generation  
   - Reddit API Credentials → for fetching posts  
   - Discord Webhook URL → for notifications (optional)

4. **Run or Schedule the Workflow**  
   - Click **Execute Workflow** for manual run  
   - Or schedule weekly execution using the **Schedule Trigger** node.

---

## 🧭 Example Use Case

This workflow can be used by marketing and AI teams to:
- Automatically generate creative ad copy.
- Identify which messages perform best in real-world social media.
- Export structured engagement reports.
- Keep teams updated automatically on Discord.

---

## 👤 Author

**Aneesh Koka**  
AI Engineer | Workflow Automation & Intelligent Systems  
📍 Boston, MA  
🔗 [GitHub: aneeshkoka](https://github.com/aneeshkoka)

---

## 📁 Repository Structure

```
n8n-content-agent-project/
│
├── content_agent_full_workflow.json   # Complete workflow export (Content + Reddit)
├── README.md                          # Project documentation
└── .gitignore                         # Optional exclusions (logs, temp files)
```

---

> 💡 *This project demonstrates how n8n can combine AI content creation with automated performance tracking — closing the loop between generation, analysis, and continuous improvement.*
