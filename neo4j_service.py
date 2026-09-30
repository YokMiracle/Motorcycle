from pathlib import Path
import json
from datetime import date
from uuid import uuid4
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
    # Only initialize rental demo once; preserve subsequent user changes.
    query("""MERGE (setup:RentalSetup {name:'motorcycle_demo_v1'})
    ON CREATE SET setup.initialized=false
    WITH setup WHERE setup.initialized=false
    UNWIND $rows AS row
    MATCH (u:User {name:row.user}), (m:Motorcycle {name:row.motorcycle})
    MERGE (u)-[r:RENTED {rental_id:'demo:' + row.user + ':' + row.motorcycle}]->(m)
    ON CREATE SET r.start_date=date('2026-09-01'), r.end_date=date('2026-09-02'),
                  r.status='returned', r.is_demo=true
    WITH DISTINCT setup SET setup.initialized=true""", {"rows":DATA["likes"]}, True)

def catalog():
    return query("MATCH (m:Motorcycle) WHERE m.name IN $models RETURN DISTINCT m.name AS name, m.image_url AS image_url, m.image_data AS image_data ORDER BY name", {"models":MODELS})

def liked(user):
    return query("MATCH (:User {name:$user})-[:RENTED]->(m:Motorcycle) WHERE m.name IN $models RETURN DISTINCT m.name AS name, m.image_url AS image_url, m.image_data AS image_data ORDER BY name", {"user":user,"models":MODELS})

RECOMMEND = """
MATCH (me:User {name:$user})-[:RENTED]->(shared:Motorcycle)<-[:RENTED]-(other:User)-[:RENTED]->(rec:Motorcycle)
WHERE other <> me AND other.name IN $users AND shared.name IN $models AND rec.name IN $models
AND NOT EXISTS { (me)-[:RENTED]->(rec) }
WITH DISTINCT shared, other, rec
RETURN rec.name AS name, rec.image_url AS image_url, rec.image_data AS image_data,
       count(*) AS score, collect(DISTINCT other.name) AS similar_users,
       collect(DISTINCT shared.name) AS shared_models
ORDER BY score DESC, name ASC LIMIT $limit
"""
def recommend(user, limit=6):
    return query(RECOMMEND, {"user":user,"users":USERS,"models":MODELS,"limit":int(limit)})

def rental_history(user):
    return query("""MATCH (:User {name:$user})-[r:RENTED]->(m:Motorcycle)
    WHERE m.name IN $models
    RETURN r.rental_id AS rental_id, m.name AS name, toString(r.start_date) AS start_date,
           toString(r.end_date) AS end_date, r.status AS status, r.rating AS rating,
           coalesce(r.is_demo,false) AS is_demo
    ORDER BY start_date DESC, rental_id""", {"user":user,"models":MODELS})

def record_rental(user, model, start, end, rating=None):
    if user not in USERS or model not in MODELS:
        raise ValueError("ไม่พบผู้ใช้หรือรุ่นรถ")
    if date.fromisoformat(end) < date.fromisoformat(start):
        raise ValueError("วันคืนรถต้องไม่ก่อนวันเริ่มเช่า")
    if rating is not None and not 1 <= float(rating) <= 5:
        raise ValueError("คะแนนต้องอยู่ระหว่าง 1–5")
    rid=str(uuid4())
    query("""MATCH (u:User {name:$user}), (m:Motorcycle {name:$model})
    CREATE (u)-[r:RENTED {rental_id:$id}]->(m)
    SET r.start_date=date($start), r.end_date=date($end), r.status='active', r.is_demo=false
    """, {"user":user,"model":model,"id":rid,"start":start,"end":end}, True)
    return rid

def return_rental(user, rental_id, rating=None):
    if rating is not None and not 1 <= float(rating) <= 5:
        raise ValueError("คะแนนต้องอยู่ระหว่าง 1–5")
    query("""MATCH (:User {name:$user})-[r:RENTED {rental_id:$id}]->(:Motorcycle)
    SET r.status='returned', r.returned_at=datetime()
    FOREACH (_ IN CASE WHEN $rating IS NULL THEN [] ELSE [1] END | SET r.rating=$rating)
    """, {"user":user,"id":rental_id,"rating":rating}, True)

def save_image(model, url="", image_data=""):
    if model not in MODELS:
        raise ValueError("Unknown motorcycle")
    query("MATCH (m:Motorcycle {name:$model}) SET m.image_url=$url, m.image_data=$data", {"model":model,"url":url,"data":image_data}, True)
