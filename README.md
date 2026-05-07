# Finance AI Agent

An AI agent for Financial Planning and Analysis. Finance teams can ask questions about budgets, revenue, cash flow and risks in plain English instead of manually working through spreadsheets.

## Tech Stack

- Neo4j - graph database for org structure
- Milvus - vector database for report search
- Ollama with LLaMA 3.2 - local language model
- nomic-embed-text - embedding model
- LangChain and LangGraph - agent framework
- Gradio - web interface
- Docker - runs Neo4j and Milvus containers

## Tools

The agent has 9 tools it selects from based on the question:

- Calculator - math
- BudgetAnalysis - budget vs actual by department
- RevenueAnalysis - revenue by product vs target
- CashFlowAnalysis - cash flow and runway
- BudgetRisk - department budget risk scoring
- RevenueRisk - product revenue risk scoring
- OperationalRisk - operational risk register
- OrgStructure - company structure and department heads
- ReportSearch - search CFO commentaries and reports

## How to Run

Install Docker, Python 3.11 and Ollama. Then run:

docker compose up -d
ollama pull llama3.2
ollama pull nomic-embed-text
python3.11 setup_graph.py
python3.11 setup_milvus.py
python3.11 app.py

## Example Questions

- Which department has the highest budget variance?
- What is our cash runway?
- Which product is at risk of missing its target?
- What did the CFO say about marketing?
- Who leads the IT department?
- Show me all operational risks

## Note

Uses dummy data for a fictional company called TechCorp for demonstration purposes.
