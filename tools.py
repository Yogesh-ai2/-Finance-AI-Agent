import json
import pandas as pd
from langchain_core.tools import Tool
from langchain_ollama import OllamaEmbeddings
from pymilvus import connections, Collection
from neo4j import GraphDatabase

uri = "bolt://localhost:7689"
auth = ("neo4j", "fpnatech2024")


def calculator_tool(expr):
    try:
        ok = set("0123456789+-*/().% ")
        if not all(c in ok for c in expr):
            return "Invalid expression."
        return "Result: " + str(eval(expr))
    except Exception as e:
        return "Error: " + str(e)


def budget_analysis_tool(query):
    try:
        df = pd.read_csv("data/budget_actual.csv")
        out = "Budget vs Actual Analysis:\n"
        for dept in df["department"].unique():
            d = df[df["department"] == dept]
            tb = d["budget"].sum()
            ta = d["actual"].sum()
            v = ta - tb
            vp = (v / tb) * 100
            out += "\n" + dept + ": Budget $" + str(int(tb)) + " | Actual $" + str(int(ta)) + " | Variance $" + str(int(v)) + " (" + str(round(vp,1)) + "%)"
        return out
    except Exception as e:
        return "Error: " + str(e)


def revenue_analysis_tool(query):
    try:
        df = pd.read_csv("data/revenue.csv")
        out = "Revenue Analysis:\n"
        for prod in df["product"].unique():
            d = df[df["product"] == prod]
            ta = d["actual"].sum()
            tt = d["target"].sum()
            ach = (ta / tt) * 100
            out += "\n" + prod + ": Actual $" + str(int(ta)) + " | Target $" + str(int(tt)) + " | Achievement " + str(round(ach,1)) + "%"
        return out
    except Exception as e:
        return "Error: " + str(e)


def cashflow_analysis_tool(query):
    try:
        df = pd.read_csv("data/cashflow.csv")
        ocf = df["operating"].sum()
        avg = df["operating"].mean()
        cb = df["closing_balance"].iloc[-1]
        net_avg = df["net"].mean()
        runway = cb / abs(net_avg) if net_avg != 0 else 999
        return "Cash Flow Analysis:\nTotal Operating CF: $" + str(int(ocf)) + "\nAverage Monthly OCF: $" + str(int(avg)) + "\nClosing Balance: $" + str(int(cb)) + "\nRunway: " + str(round(runway,1)) + " months"
    except Exception as e:
        return "Error: " + str(e)


def budget_risk_tool(query):
    try:
        df = pd.read_csv("data/budget_actual.csv")
        with open("data/risk_thresholds.json") as f:
            t = json.load(f)
        out = "Budget Risk Assessment:\n"
        for dept in df["department"].unique():
            d = df[df["department"] == dept]
            tb = d["budget"].sum()
            ta = d["actual"].sum()
            vp = ((ta - tb) / tb) * 100
            if vp > t["budget"]["medium_pct"]:
                risk = "HIGH"
            elif vp > t["budget"]["low_pct"]:
                risk = "MEDIUM"
            else:
                risk = "LOW"
            out += "\n" + dept + ": " + risk + " (" + str(round(vp,1)) + "% vs budget)"
        return out
    except Exception as e:
        return "Error: " + str(e)


def revenue_risk_tool(query):
    try:
        df = pd.read_csv("data/revenue.csv")
        with open("data/risk_thresholds.json") as f:
            t = json.load(f)
        out = "Revenue Risk Assessment:\n"
        for prod in df["product"].unique():
            d = df[df["product"] == prod]
            ach = (d["actual"].sum() / d["target"].sum()) * 100
            if ach < t["revenue"]["medium_pct"]:
                risk = "HIGH"
            elif ach < t["revenue"]["low_pct"]:
                risk = "MEDIUM"
            else:
                risk = "LOW"
            out += "\n" + prod + ": " + risk + " (" + str(round(ach,1)) + "% achievement)"
        return out
    except Exception as e:
        return "Error: " + str(e)


def operational_risk_tool(query):
    try:
        with open("data/operational_risks.json") as f:
            risks = json.load(f)
        out = "Operational Risks:\n"
        for r in risks:
            out += "\n" + r["area"] + " - " + r["risk_type"] + " - " + r["score"] + "\n  " + r["description"] + "\n  Mitigation: " + r["mitigation"] + "\n"
        return out
    except Exception as e:
        return "Error: " + str(e)


def graphrag_tool(query):
    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        out = ""
        with driver.session() as s:
            q = query.lower()
            if "department" in q or "head" in q:
                res = s.run("MATCH (e:Employee)-[:LEADS]->(d:Department) RETURN e.name as head, d.name as dept, d.budget as budget")
                for r in res:
                    out += r["head"] + " leads " + r["dept"] + " (Budget: $" + str(r["budget"]) + ")\n"
            elif "unit" in q or "structure" in q:
                res = s.run("MATCH (b:BusinessUnit)-[:HAS_DEPT]->(d:Department) RETURN b.name as unit, d.name as dept")
                for r in res:
                    out += r["unit"] + " -> " + r["dept"] + "\n"
            else:
                res = s.run("MATCH (c:Company)-[:HAS_UNIT]->(b)-[:HAS_DEPT]->(d) RETURN c.name as comp, b.name as unit, d.name as dept LIMIT 20")
                for r in res:
                    out += r["comp"] + " > " + r["unit"] + " > " + r["dept"] + "\n"
        driver.close()
        return out if out else "No results."
    except Exception as e:
        return "Error: " + str(e)


def report_rag_tool(query):
    try:
        connections.connect(host="localhost", port="19532")
        col = Collection("fpna_reports")
        col.load()
        emb = OllamaEmbeddings(model="nomic-embed-text")
        vec = emb.embed_query(query)
        hits = col.search(
            data=[vec],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=2,
            output_fields=["report_name", "content"]
        )
        out = "From Financial Reports:\n"
        for h in hits[0]:
            out += "\n" + h.entity.get("report_name") + ":\n" + h.entity.get("content") + "\n"
        return out
    except Exception as e:
        return "Error: " + str(e)


def get_all_tools():
    return [
        Tool(name="Calculator", func=calculator_tool, description="Use for math calculations. Input math expression."),
        Tool(name="BudgetAnalysis", func=budget_analysis_tool, description="Use for budget vs actual analysis by department."),
        Tool(name="RevenueAnalysis", func=revenue_analysis_tool, description="Use for revenue analysis by product vs target."),
        Tool(name="CashFlowAnalysis", func=cashflow_analysis_tool, description="Use for cash flow analysis and runway calculation."),
        Tool(name="BudgetRisk", func=budget_risk_tool, description="Use for budget risk scoring of departments."),
        Tool(name="RevenueRisk", func=revenue_risk_tool, description="Use for revenue risk scoring of products."),
        Tool(name="OperationalRisk", func=operational_risk_tool, description="Use for operational risk register and mitigation."),
        Tool(name="OrgStructure", func=graphrag_tool, description="Use for questions about company structure, departments, business units, department heads."),
        Tool(name="ReportSearch", func=report_rag_tool, description="Use for searching CFO commentaries and financial reports."),
    ]
