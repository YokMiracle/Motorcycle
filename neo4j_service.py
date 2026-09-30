from pathlib import Path
import json
import streamlit as st
from neo4j import GraphDatabase, RoutingControl

DATA = json.loads((Path(__file__).parent / "data.json").read_text())
USERS = DATA["users"]
MODELS = [m["name"] for m in DATA["motorcycles"]]

@st.cache_resource
def get_driver():
    cfg = st.secrets["neo4j"]
    driver = GraphDatabase.driver(cfg["uri"], auth=(cfg["username"], cfg["password"]))
    driver.verify_connectivity()
    return driver

def query(cypher, parameters=None, write=False):
    rows, _, _ = get_driver().execute_query(cypher, parameters_=parameters or {},
        database_=st.secrets["neo4j"].get("database", "neo4j"),
        routing_=RoutingControl.WRITE if write else RoutingControl.READ)
    return [r.data() for r in rows]

def seed_demo_data():
    for label in ("User", "Motorcycle"):
        query(f"CREATE CONSTRAINT {label.lower()}_name_unique IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE", write=True)
    query("UNWIND $names AS name MERGE (:User {name:name})", {"names":USERS}, True)
    query("UNWIND $rows AS row MERGE (m:Motorcycle {name:row.name}) SET m.image_url = coalesce(m.image_url, row.image_url), m.image_data = CASE WHEN coalesce(m.image_data, "") = "" AND coalesce(m.image_url, "") = "" THEN row.image_data ELSE m.image_data END", {"rows":DATA["motorcycles"]}, True)
    query("UNWIND $rows AS row MATCH (u:User {name:row.user}), (m:Motorcycle {name:row.motorcycle}) MERGE (u)-[:LIKES]->(m)", {"rows":DATA["likes"]}, True)

def catalog():
    return query("MATCH (m:Motorcycle) WHERE m.name IN $models RETURN m.name AS name, m.image_url AS image_url, m.image_data AS image_data ORDER BY name", {"models":MODELS})

def liked(user):
    return query("MATCH (:User {name:$user})-[:LIKES]->(m:Motorcycle) WHERE m.name IN $models RETURN m.name AS name, m.image_url AS image_url, m.image_data AS image_data ORDER BY name", {"user":user,"models":MODELS})

RECOMMEND = """
MATCH (me:User {name:$user})-[:LIKES]->(shared:Motorcycle)<-[:LIKES]-(other:User)-[:LIKES]->(rec:Motorcycle)
WHERE other <> me AND other.name IN $users AND shared.name IN $models AND rec.name IN $models
AND NOT EXISTS { (me)-[:LIKES]->(rec) }
RETURN rec.name AS name, rec.image_url AS image_url, rec.image_data AS image_data,
       count(*) AS score, collect(DISTINCT other.name) AS similar_users,
       collect(DISTINCT shared.name) AS shared_models
ORDER BY score DESC, name ASC LIMIT $limit
"""
def recommend(user, limit=6):
    return query(RECOMMEND, {"user":user,"users":USERS,"models":MODELS,"limit":int(limit)})

def set_like(user, model, enabled):
    if user not in USERS or model not in MODELS:
        raise ValueError("Unknown user or motorcycle")
    statement = "MERGE (u)-[:LIKES]->(m)" if enabled else "WITH u,m MATCH (u)-[r:LIKES]->(m) DELETE r"
    query("MATCH (u:User {name:$user}), (m:Motorcycle {name:$model}) " + statement, {"user":user,"model":model}, True)

def save_image(model, url="", image_data=""):
    if model not in MODELS:
        raise ValueError("Unknown motorcycle")
    query("MATCH (m:Motorcycle {name:$model}) SET m.image_url=$url, m.image_data=$data", {"model":model,"url":url,"data":image_data}, True)
