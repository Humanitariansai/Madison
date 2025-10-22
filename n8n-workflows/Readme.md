## Madison — n8n Workflows for Agent Layers

This file is a compact index describing what each agent-layer workflow does and what it needs. Each entry is short — detailed usage and run instructions live in per-folder READMEs.

1) Intelligence Agents
- Purpose: collect and normalize data from feeds, social APIs, news, and other sources; perform initial enrichment and store or forward results.
- Inputs: RSS/HTTP endpoints, scheduled scrapes, webhooks.
- Outputs: normalized JSON, CSV exports, Google Sheets rows, alerts via webhooks/Discord.
- Key nodes: HTTP Request, Schedule/Cron, Split/Batch, Code (parsing/normalization), Google Sheets/MySQL, Respond to Webhook.
- Credentials: source API keys, Google Sheets, DB credentials, optional LLM creds for summarization.

2) Content Agents
- Purpose: accept briefs, build LLM prompts, generate variants, run QA, export approved content and visual prompts.
- Inputs: brief webhook (JSON), scheduled briefs, brand voice objects.
- Outputs: variants JSON/CSV, approved vs needs-review exports, visual concept prompts, notifications.
- Key nodes: Webhook, Set, Code, OpenAI/LLM nodes, ConvertToFile, RespondToWebhook, HTTP Request.
- Credentials: OpenAI/LLM keys, webhook/Discord, storage or Google Sheets.

3) Research / Survey Agents
- Purpose: ingest survey files, preprocess responses, run analyses (themes, sentiment), produce reports and charts.
- Inputs: uploaded CSVs, scheduled pulls, dataset webhooks.
- Outputs: analysis JSON, charts, Google Sheets updates, Slack/Discord summaries, report files.
- Key nodes: ExtractFromFile, Code (preproc), OpenAI/LLM nodes, ConvertToFile, Google Sheets, Slack/Discord.
- Credentials: survey platform APIs, Google Sheets, Slack, LLM creds.

4) Experience Agents
- Purpose: automate concierge and customer workflows — route requests, recommend actions, escalate to humans.
- Inputs: chat/webhook requests, CRM events, user profile updates.
- Outputs: conversational responses, routed tickets, CRM updates, logs.
- Key nodes: Webhook, HTTP Request (CRM), Code (business logic), OpenAI (optional), RespondToWebhook.
- Credentials: CRM/API keys, support system creds, optional LLM keys.

5) Performance Agents
- Purpose: measure and optimize experiments/campaigns (bandits), forecast metrics, alert on anomalies.
- Inputs: analytics feeds, scheduled pulls, campaign webhooks.
- Outputs: allocation decisions, reports, alerts, dashboard updates.
- Key nodes: ScheduleTrigger, Code (scoring/decision), HTTP Request, Database/Sheets, RespondToWebhook.
- Credentials: analytics APIs, DB credentials, dashboard/Grafana keys, optional LLM creds.

Repository examples
- `Content_Agent_full_workflow.json` — content pipeline example
- `SurveyAnalysis/workflow.json` — survey -> analysis pipeline
- `MarketMind/n8n-marketminds-workflow.json` — orchestration / executor
- `Intelligence-Agent/n8_workflow.json` — intelligence collection example

Quick import note
- Import any workflow JSON into n8n via the Import feature, configure credentials in the editor, test nodes individually, then enable the workflow.

Want per-folder READMEs?
- I can generate concise READMEs for selected folders (e.g., Content-Agent, Intelligence-Agent, Research-Agent). Tell me which folders to generate first and I'll create them with required env vars, sample inputs, and a short test checklist.

