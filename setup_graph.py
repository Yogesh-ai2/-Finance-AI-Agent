import json
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7689", auth=("neo4j", "fpnatech2024"))

def q(query, params={}):
    with driver.session() as s:
        s.run(query, params)

with open("data/company.json") as f:
    company = json.load(f)

with open("data/departments.json") as f:
    depts = json.load(f)

q("MERGE (c:Company {name: $name}) SET c.industry=$ind, c.currency=$cur, c.target=$tgt",
  {"name": company["name"], "ind": company["industry"], "cur": company["currency"], "tgt": company["annual_revenue_target"]})

units = set()
for d in depts:
    units.add(d["unit"])

for u in units:
    q("MERGE (b:BusinessUnit {name: $name})", {"name": u})
    q("MATCH (c:Company {name: $cname}), (b:BusinessUnit {name: $bname}) MERGE (c)-[:HAS_UNIT]->(b)",
      {"cname": company["name"], "bname": u})

for d in depts:
    q("MERGE (dept:Department {name: $name}) SET dept.budget=$bud, dept.head=$head",
      {"name": d["name"], "bud": d["budget"], "head": d["head"]})
    q("MATCH (b:BusinessUnit {name: $bname}), (dept:Department {name: $dname}) MERGE (b)-[:HAS_DEPT]->(dept)",
      {"bname": d["unit"], "dname": d["name"]})
    q("MERGE (e:Employee {name: $name})", {"name": d["head"]})
    q("MATCH (e:Employee {name: $ename}), (dept:Department {name: $dname}) MERGE (e)-[:LEADS]->(dept)",
      {"ename": d["head"], "dname": d["name"]})

with driver.session() as s:
    print("Companies:", s.run("MATCH (c:Company) RETURN count(c) as n").single()["n"])
    print("Units:", s.run("MATCH (b:BusinessUnit) RETURN count(b) as n").single()["n"])
    print("Departments:", s.run("MATCH (d:Department) RETURN count(d) as n").single()["n"])
    print("Employees:", s.run("MATCH (e:Employee) RETURN count(e) as n").single()["n"])
    print("Relationships:", s.run("MATCH ()-[r]->() RETURN count(r) as n").single()["n"])

driver.close()
