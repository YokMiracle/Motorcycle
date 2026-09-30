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
    query("""MERGE (setup:RentalSetup {name:'motorcycle_ratings_demo_v2'})
    ON CREATE SET setup.initialized=false
    WITH setup WHERE setup.initialized=false
    UNWIND $rows AS row
    MATCH (u:User {name:row.user}), (m:Motorcycle {name:row.motorcycle})
    MERGE (u)-[r:RENTED {rental_id:'demo:' + row.user + ':' + row.motorcycle}]->(m)
    SET r.rental_date=date(row.rental_date), r.rating=row.rating,
                  r.status='completed', r.is_demo=true
    WITH DISTINCT setup SET setup.initialized=true""", {"rows":[dict(row, rental_date=f"2026-09-{i+1:02d}", rating=[4.5,4.0,5.0,3.5][i % 4]) for i,row in enumerate(DATA["likes"])]}, True)

def catalog():
    # Return both original demo motorcycles and motorcycles added from the UI.
    return query("MATCH (m:Motorcycle) RETURN DISTINCT m.name AS name, m.image_url AS image_url, m.image_data AS image_data ORDER BY name")

def all_models():
    return [row["name"] for row in catalog()]

def add_motorcycle(name, url="", image_data=""):
    name = (name or "").strip()
    if not name:
        raise ValueError("กรุณากรอกชื่อรถ")
    query("""MERGE (m:Motorcycle {name:$name})
    ON CREATE SET m.created_at=datetime()
    SET m.image_url=$url, m.image_data=$data, m.is_custom=true
    """, {"name":name, "url":url, "data":image_data}, True)
    return name

def liked(user):
    return query("MATCH (:User {name:$user})-[:RENTED]->(m:Motorcycle) RETURN DISTINCT m.name AS name, m.image_url AS image_url, m.image_data AS image_data ORDER BY name", {"user":user})

RECOMMEND = """
MATCH (me:User {name:$user})-[:RENTED]->(shared:Motorcycle)<-[:RENTED]-(other:User)-[:RENTED]->(rec:Motorcycle)
WHERE other <> me AND other.name IN $users
AND NOT EXISTS { (me)-[:RENTED]->(rec) }
WITH DISTINCT shared, other, rec
WITH rec, count(*) AS path_count, collect(DISTINCT other.name) AS similar_users,
     collect(DISTINCT shared.name) AS shared_models
OPTIONAL MATCH (reviewer:User)-[review:RENTED]->(rec)
WHERE reviewer.name IN $users AND review.rating IS NOT NULL
WITH rec,path_count,similar_users,shared_models,avg(review.rating) AS avg_rating,count(review) AS rating_count
RETURN rec.name AS name, rec.image_url AS image_url, rec.image_data AS image_data,
       path_count, similar_users, shared_models, coalesce(avg_rating,0.0) AS avg_rating, rating_count,
       path_count * 3.0 + coalesce(avg_rating,0.0) * 0.5 AS score
ORDER BY score DESC, name ASC LIMIT $limit
"""

def recommend(user, limit=6):
    return query(RECOMMEND, {"user":user,"users":USERS,"limit":int(limit)})

def rental_history(user):
    return query("""MATCH (:User {name:$user})-[r:RENTED]->(m:Motorcycle)
    RETURN r.rental_id AS rental_id, m.name AS name, toString(coalesce(r.rental_date,r.start_date)) AS rental_date, r.rating AS rating,
           coalesce(r.is_demo,false) AS is_demo
    ORDER BY rental_date DESC, rental_id""", {"user":user})

def record_rental(user, model, rental_date, rating):
    if user not in USERS or model not in all_models():
        raise ValueError("ไม่พบผู้ใช้หรือรุ่นรถ")
    if date.fromisoformat(rental_date) > date.today():
        raise ValueError("วันที่เคยเช่าต้องไม่เป็นวันในอนาคต")
    if rating is None or not 1 <= float(rating) <= 5:
        raise ValueError("คะแนนต้องอยู่ระหว่าง 1–5")
    rid=str(uuid4())
    query("""MATCH (u:User {name:$user}), (m:Motorcycle {name:$model})
    CREATE (u)-[r:RENTED {rental_id:$id}]->(m)
    SET r.rental_date=date($date), r.rating=$rating, r.status='completed', r.is_demo=false
    """, {"user":user,"model":model,"id":rid,"date":rental_date,"rating":float(rating)}, True)
    return rid

def save_image(model, url="", image_data=""):
    if model not in all_models():
        raise ValueError("Unknown motorcycle")
    query("MATCH (m:Motorcycle {name:$model}) SET m.image_url=$url, m.image_data=$data", {"model":model,"url":url,"data":image_data}, True)
