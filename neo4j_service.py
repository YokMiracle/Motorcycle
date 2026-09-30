from pathlib import Path
import json
from datetime import date
import streamlit as st
from neo4j import GraphDatabase, RoutingControl

DATA = json.loads((Path(__file__).parent / 'data.json').read_text())
SEED_USERS = DATA['users']
SEED_MODELS = DATA['motorcycles']
SEED_LIKES = DATA['likes']

@st.cache_resource
def get_driver():
    cfg = st.secrets['neo4j']
    d = GraphDatabase.driver(cfg['uri'], auth=(cfg['username'], cfg['password']))
    d.verify_connectivity()
    return d

def query(cypher, parameters=None, write=False):
    rows, _, _ = get_driver().execute_query(
        cypher, parameters_=parameters or {},
        database_=st.secrets['neo4j'].get('database', 'neo4j'),
        routing_=RoutingControl.WRITE if write else RoutingControl.READ)
    return [r.data() for r in rows]

def users():
    return [x['name'] for x in query('MATCH (u:User) RETURN u.name AS name ORDER BY name')]

def models():
    return [x['name'] for x in query('MATCH (m:Motorcycle) RETURN m.name AS name ORDER BY name')]

def setup_data():
    query('CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (n:User) REQUIRE n.name IS UNIQUE', write=True)
    query('CREATE CONSTRAINT motorcycle_name_unique IF NOT EXISTS FOR (n:Motorcycle) REQUIRE n.name IS UNIQUE', write=True)
    query('UNWIND $names AS name MERGE (:User {name:name})', {'names': SEED_USERS}, True)
    query('''UNWIND $rows AS row MERGE (m:Motorcycle {name:row.name})
             SET m.image_url=coalesce(m.image_url,row.image_url),
                 m.image_data=CASE WHEN coalesce(m.image_data,'')='' AND coalesce(m.image_url,'')='' THEN row.image_data ELSE m.image_data END''', {'rows': SEED_MODELS}, True)
    query('''UNWIND $rows AS row MATCH (u:User {name:row.user}),(m:Motorcycle {name:row.motorcycle})
             MERGE (u)-[r:LIKES]->(m)
             ON CREATE SET r.rating=4.0, r.liked_at=date('2026-09-01'), r.source='seed' ''', {'rows': SEED_LIKES}, True)
    # Preserve earlier project data by copying RENTED into LIKES.
    query('''MATCH (u:User)-[old:RENTED]->(m:Motorcycle)
             MERGE (u)-[r:LIKES]->(m)
             SET r.rating=coalesce(r.rating,old.rating,4.0),
                 r.liked_at=coalesce(r.liked_at,old.rental_date,date()),
                 r.source=coalesce(r.source,'migrated')''', write=True)

def catalog():
    return query('''MATCH (m:Motorcycle)
        OPTIONAL MATCH (:User)-[r:LIKES]->(m)
        RETURN m.name AS name,m.image_url AS image_url,m.image_data AS image_data,
               coalesce(avg(r.rating),0.0) AS avg_rating,count(r) AS like_count
        ORDER BY like_count DESC,name''')

def user_profile(user):
    rows=query('''MATCH (u:User {name:$u}) OPTIONAL MATCH (u)-[r:LIKES]->(m:Motorcycle)
        RETURN u.name AS name,count(r) AS likes,coalesce(avg(r.rating),0.0) AS avg_rating''',{'u':user})
    return rows[0] if rows else {'name':user,'likes':0,'avg_rating':0.0}

def liked(user):
    return query('''MATCH (:User {name:$u})-[r:LIKES]->(m:Motorcycle)
        RETURN m.name AS name,m.image_url AS image_url,m.image_data AS image_data,
               r.rating AS rating,toString(r.liked_at) AS liked_at ORDER BY r.liked_at DESC,m.name''',{'u':user})

def recommend(user, limit=6):
    return query('''MATCH (me:User {name:$u})-[:LIKES]->(shared:Motorcycle)<-[:LIKES]-(other:User)-[ol:LIKES]->(rec:Motorcycle)
        WHERE other<>me AND NOT EXISTS {(me)-[:LIKES]->(rec)}
        WITH rec, count(DISTINCT other) AS similar_count,
             collect(DISTINCT other.name) AS similar_users,
             collect(DISTINCT shared.name) AS shared_models,
             avg(coalesce(ol.rating,4.0)) AS peer_rating
        OPTIONAL MATCH (:User)-[allr:LIKES]->(rec)
        WITH rec,similar_count,similar_users,shared_models,peer_rating,
             coalesce(avg(allr.rating),0.0) AS avg_rating,count(allr) AS like_count
        WITH rec,similar_count,similar_users,shared_models,avg_rating,like_count,
             similar_count*3.0 + peer_rating*1.2 + log(1+like_count) AS score
        RETURN rec.name AS name,rec.image_url AS image_url,rec.image_data AS image_data,
               similar_users,shared_models,avg_rating,like_count,score
        ORDER BY score DESC,like_count DESC,name LIMIT $limit''', {'u':user,'limit':int(limit)})

def save_preference(user, model, rating, liked_at=None):
    if user not in users() or model not in models():
        raise ValueError('ไม่พบผู้ใช้หรือรุ่นรถ')
    d = liked_at or date.today().isoformat()
    query('''MATCH (u:User {name:$u}),(m:Motorcycle {name:$m})
        MERGE (u)-[r:LIKES]->(m)
        SET r.rating=$rating,r.liked_at=date($d),r.source='user' ''',
        {'u':user,'m':model,'rating':float(rating),'d':d},True)

def remove_preference(user, model):
    query('MATCH (:User {name:$u})-[r:LIKES]->(:Motorcycle {name:$m}) DELETE r',{'u':user,'m':model},True)

def history(user):
    return query('''MATCH (:User {name:$u})-[r:LIKES]->(m:Motorcycle)
        RETURN m.name AS motorcycle,r.rating AS rating,toString(r.liked_at) AS date
        ORDER BY r.liked_at DESC,m.name''',{'u':user})

def graph_edges(user=None):
    if user:
        return query('''MATCH (u:User {name:$u})-[r:LIKES]->(m:Motorcycle)
            RETURN u.name AS user,m.name AS motorcycle,r.rating AS rating,toString(r.liked_at) AS date
            ORDER BY motorcycle''',{'u':user})
    return query('''MATCH (u:User)-[r:LIKES]->(m:Motorcycle)
        RETURN u.name AS user,m.name AS motorcycle,r.rating AS rating,toString(r.liked_at) AS date
        ORDER BY user,motorcycle''')

def stats():
    rows=query('''MATCH (u:User) WITH count(u) AS users
        MATCH (m:Motorcycle) WITH users,count(m) AS motorcycles
        OPTIONAL MATCH (:User)-[r:LIKES]->(:Motorcycle)
        RETURN users,motorcycles,count(r) AS likes,coalesce(avg(r.rating),0.0) AS avg_rating''')
    return rows[0] if rows else {'users':0,'motorcycles':0,'likes':0,'avg_rating':0}

def popular(limit=5):
    return query('''MATCH (m:Motorcycle) OPTIONAL MATCH (:User)-[r:LIKES]->(m)
        RETURN m.name AS name,m.image_url AS image_url,m.image_data AS image_data,
               count(r) AS like_count,coalesce(avg(r.rating),0.0) AS avg_rating
        ORDER BY like_count DESC,avg_rating DESC,name LIMIT $limit''',{'limit':int(limit)})

def add_motorcycle(name,url='',image_data=''):
    name=name.strip()
    if not name: raise ValueError('กรุณาใส่ชื่อรถ')
    query('MERGE (m:Motorcycle {name:$n}) SET m.image_url=$url,m.image_data=$data',{'n':name,'url':url,'data':image_data},True)

def delete_motorcycle(name):
    query('MATCH (m:Motorcycle {name:$n}) DETACH DELETE m',{'n':name},True)

def save_image(model,url='',image_data=''):
    query('MATCH (m:Motorcycle {name:$m}) SET m.image_url=$url,m.image_data=$data',{'m':model,'url':url,'data':image_data},True)

def add_user(name):
    name=name.strip()
    if not name: raise ValueError('กรุณาใส่ชื่อผู้ใช้')
    query('MERGE (:User {name:$n})',{'n':name},True)

def delete_user(name):
    query('MATCH (u:User {name:$n}) DETACH DELETE u',{'n':name},True)
