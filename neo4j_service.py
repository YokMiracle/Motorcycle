from pathlib import Path
import json
from datetime import date
from uuid import uuid4
import streamlit as st
from neo4j import GraphDatabase, RoutingControl

DATA = json.loads((Path(__file__).parent / 'data.json').read_text())
SEED_USERS = DATA['users']
SEED_MODELS = [m['name'] for m in DATA['motorcycles']]

@st.cache_resource
def get_driver():
    cfg=st.secrets['neo4j']
    d=GraphDatabase.driver(cfg['uri'], auth=(cfg['username'],cfg['password']))
    d.verify_connectivity(); return d

def query(cypher, parameters=None, write=False):
    rows,_,_=get_driver().execute_query(cypher, parameters_=parameters or {}, database_=st.secrets['neo4j'].get('database','neo4j'), routing_=RoutingControl.WRITE if write else RoutingControl.READ)
    return [r.data() for r in rows]

def users(): return [x['name'] for x in query('MATCH (u:User) RETURN u.name AS name ORDER BY name')]
def models(): return [x['name'] for x in query('MATCH (m:Motorcycle) RETURN m.name AS name ORDER BY name')]

def seed_demo_data():
    query('CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (n:User) REQUIRE n.name IS UNIQUE',write=True)
    query('CREATE CONSTRAINT motorcycle_name_unique IF NOT EXISTS FOR (n:Motorcycle) REQUIRE n.name IS UNIQUE',write=True)
    query('UNWIND $names AS name MERGE (:User {name:name})',{'names':SEED_USERS},True)
    query('UNWIND $rows AS row MERGE (m:Motorcycle {name:row.name}) SET m.image_url=coalesce(m.image_url,row.image_url), m.image_data=CASE WHEN coalesce(m.image_data,"")="" AND coalesce(m.image_url,"")="" THEN row.image_data ELSE m.image_data END',{'rows':DATA['motorcycles']},True)
    demo=[dict(r,rental_date=f'2026-09-{i+1:02d}',rating=[4.5,4.0,5.0,3.5][i%4]) for i,r in enumerate(DATA['likes'])]
    query('''MERGE (s:RentalSetup {name:'motorcycle_ratings_demo_v3'}) ON CREATE SET s.initialized=false
    WITH s WHERE s.initialized=false UNWIND $rows AS row MATCH (u:User {name:row.user}),(m:Motorcycle {name:row.motorcycle})
    MERGE (u)-[r:RENTED {rental_id:'demo:'+row.user+':'+row.motorcycle}]->(m)
    SET r.rental_date=date(row.rental_date),r.rating=row.rating,r.status='completed',r.is_demo=true
    WITH DISTINCT s SET s.initialized=true''',{'rows':demo},True)

def catalog(): return query('MATCH (m:Motorcycle) RETURN m.name AS name,m.image_url AS image_url,m.image_data AS image_data ORDER BY name')
def liked(user): return query('MATCH (:User {name:$u})-[:RENTED]->(m:Motorcycle) RETURN DISTINCT m.name AS name,m.image_url AS image_url,m.image_data AS image_data ORDER BY name',{'u':user})

def rental_history(user):
    return query('''MATCH (:User {name:$u})-[r:RENTED]->(m:Motorcycle)
    RETURN r.rental_id AS rental_id,m.name AS name,toString(coalesce(r.rental_date,r.start_date)) AS rental_date,r.rating AS rating,coalesce(r.is_demo,false) AS is_demo
    ORDER BY rental_date DESC,rental_id''',{'u':user})

def recommend(user,limit=6):
    return query('''MATCH (me:User {name:$u})-[:RENTED]->(shared:Motorcycle)<-[:RENTED]-(other:User)-[:RENTED]->(rec:Motorcycle)
    WHERE other<>me AND NOT EXISTS {(me)-[:RENTED]->(rec)}
    WITH rec,count(DISTINCT other) AS similar_count,collect(DISTINCT other.name) AS similar_users,collect(DISTINCT shared.name) AS shared_models
    OPTIONAL MATCH (:User)-[rv:RENTED]->(rec) WHERE rv.rating IS NOT NULL
    WITH rec,similar_count,similar_users,shared_models,avg(rv.rating) AS avg_rating,count(rv) AS rating_count
    RETURN rec.name AS name,rec.image_url AS image_url,rec.image_data AS image_data,similar_users,shared_models,coalesce(avg_rating,0.0) AS avg_rating,rating_count,
    similar_count*3.0+coalesce(avg_rating,0.0)*0.5 AS score ORDER BY score DESC,name LIMIT $limit''',{'u':user,'limit':int(limit)})

def record_rental(user,model,rental_date,rating):
    if user not in users() or model not in models(): raise ValueError('ไม่พบผู้ใช้หรือรุ่นรถ')
    if date.fromisoformat(rental_date)>date.today(): raise ValueError('วันที่เช่าต้องไม่เป็นอนาคต')
    rid=str(uuid4())
    query('''MATCH (u:User {name:$u}),(m:Motorcycle {name:$m}) CREATE (u)-[r:RENTED {rental_id:$id}]->(m)
    SET r.rental_date=date($d),r.rating=$rating,r.status='completed',r.is_demo=false''',{'u':user,'m':model,'id':rid,'d':rental_date,'rating':float(rating)},True)

def save_image(model,url='',image_data=''):
    query('MATCH (m:Motorcycle {name:$m}) SET m.image_url=$url,m.image_data=$data',{'m':model,'url':url,'data':image_data},True)

def add_motorcycle(name,url='',image_data=''):
    name=name.strip()
    if not name: raise ValueError('กรุณาใส่ชื่อรถ')
    query('MERGE (m:Motorcycle {name:$n}) SET m.image_url=$url,m.image_data=$data',{'n':name,'url':url,'data':image_data},True)

def add_user(name):
    name=name.strip()
    if not name: raise ValueError('กรุณาใส่ชื่อผู้ใช้')
    query('MERGE (:User {name:$n})',{'n':name},True)

def graph_edges(user=None):
    if user:
        return query('MATCH (u:User {name:$u})-[r:RENTED]->(m:Motorcycle) RETURN u.name AS user,m.name AS motorcycle,r.rating AS rating',{'u':user})
    return query('MATCH (u:User)-[r:RENTED]->(m:Motorcycle) RETURN u.name AS user,m.name AS motorcycle,r.rating AS rating ORDER BY user,motorcycle')
