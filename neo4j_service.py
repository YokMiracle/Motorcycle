from pathlib import Path
import json
import streamlit as st
from neo4j import GraphDatabase, RoutingControl
DATA=json.loads((Path(__file__).parent/'data.json').read_text())
@st.cache_resource
def get_driver():
 c=st.secrets['neo4j']; d=GraphDatabase.driver(c['uri'],auth=(c['username'],c['password'])); d.verify_connectivity(); return d
def query(c,p=None,w=False):
 r,_,_=get_driver().execute_query(c,parameters_=p or {},database_=st.secrets['neo4j'].get('database','neo4j'),routing_=RoutingControl.WRITE if w else RoutingControl.READ); return [x.data() for x in r]
def setup_data():
 query('CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (n:User) REQUIRE n.name IS UNIQUE',w=True); query('CREATE CONSTRAINT motorcycle_name_unique IF NOT EXISTS FOR (n:Motorcycle) REQUIRE n.name IS UNIQUE',w=True)
 query('UNWIND $x AS n MERGE (:User{name:n})',{'x':DATA['users']},True)
 query('UNWIND $x AS x MERGE (m:Motorcycle{name:x.name}) SET m.image_url=coalesce(m.image_url,x.image_url),m.image_data=coalesce(m.image_data,x.image_data),m.price=coalesce(m.price,0)',{'x':DATA['motorcycles']},True)
 query("UNWIND $x AS x MATCH (u:User{name:x.user}),(m:Motorcycle{name:x.motorcycle}) MERGE (u)-[r:ORDERED]->(m) ON CREATE SET r.ordered_at=date('2026-09-01')",{'x':DATA['likes']},True)
 # friendships generated once from users who share motorcycles, giving the demo a usable friend graph
 query('''MATCH (a:User)-[:ORDERED]->(m)<-[:ORDERED]-(b:User) WHERE a.name<b.name WITH a,b,count(DISTINCT m) s WHERE s>0 MERGE (a)-[:FRIEND]-(b)''',w=True)
 # migrate previous relations if present
 query('MATCH (u:User)-[:LIKES|RENTED]->(m:Motorcycle) MERGE (u)-[:ORDERED]->(m)',w=True)
def users(): return [x['name'] for x in query('MATCH(u:User) RETURN u.name name ORDER BY name')]
def motorcycles(): return query('MATCH(m:Motorcycle) RETURN m.name name,m.price price,m.image_url image_url,m.image_data image_data ORDER BY name')
def friends(u): return [x['name'] for x in query('MATCH(:User{name:$u})-[:FRIEND]-(f:User) RETURN f.name name ORDER BY name',{'u':u})]
def stats():
 return query('MATCH(u:User) WITH count(u) users MATCH(m:Motorcycle) WITH users,count(m) motorcycles OPTIONAL MATCH(:User)-[f:FRIEND]-(:User) WITH users,motorcycles,count(f)/2 AS friendships OPTIONAL MATCH(:User)-[o:ORDERED]->(:Motorcycle) RETURN users,motorcycles,friendships,count(o) orders')[0]
def recommendations(u):
 return query('''MATCH (me:User{name:$u})-[:FRIEND]-(f:User)-[:ORDERED]->(m:Motorcycle) WHERE NOT EXISTS {(me)-[:ORDERED]->(m)} WITH m,collect(DISTINCT f.name) friend_names,count(DISTINCT f) score RETURN m.name name,m.price price,m.image_url image_url,m.image_data image_data,friend_names,score ORDER BY score DESC,m.name''',{'u':u})
def add_user(n):
 n=n.strip();
 if n: query('MERGE(:User{name:$n})',{'n':n},True)
def add_friend(a,b):
 if a!=b: query('MATCH(a:User{name:$a}),(b:User{name:$b}) MERGE(a)-[:FRIEND]-(b)',{'a':a,'b':b},True)
def remove_friend(a,b): query('MATCH(a:User{name:$a})-[r:FRIEND]-(b:User{name:$b}) DELETE r',{'a':a,'b':b},True)
def delete_user(n): query('MATCH(u:User{name:$n}) DETACH DELETE u',{'n':n},True)
def add_motorcycle(n,price=0,url='',data=''):
 n=n.strip();
 if n: query('MERGE(m:Motorcycle{name:$n}) SET m.price=$price,m.image_url=$url,m.image_data=$data',{'n':n,'price':float(price),'url':url,'data':data},True)
def delete_motorcycle(n): query('MATCH(m:Motorcycle{name:$n}) DETACH DELETE m',{'n':n},True)
def order(u,n): query('MATCH(u:User{name:$u}),(m:Motorcycle{name:$n}) MERGE(u)-[r:ORDERED]->(m) SET r.ordered_at=date()',{'u':u,'n':n},True)
def remove_order(u,n): query('MATCH(:User{name:$u})-[r:ORDERED]->(:Motorcycle{name:$n}) DELETE r',{'u':u,'n':n},True)
def ordered(u): return query('MATCH(:User{name:$u})-[r:ORDERED]->(m:Motorcycle) RETURN m.name name,m.price price ORDER BY name',{'u':u})
def edges(person=None,show_orders=True):
 p={'u':person} if person else {}
 users_clause='MATCH(u:User{name:$u})' if person else 'MATCH(u:User)'
 fs=query(users_clause+' MATCH(u)-[:FRIEND]-(f:User) RETURN DISTINCT u.name a,f.name b',p)
 os=query(users_clause+' MATCH(u)-[:ORDERED]->(m:Motorcycle) RETURN u.name a,m.name b',p) if show_orders else []
 return fs,os
