from pathlib import Path
import json
import streamlit as st
from neo4j import GraphDatabase, RoutingControl

DATA = json.loads(
    (Path(__file__).parent / "data.json").read_text(encoding="utf-8")
)


@st.cache_resource
def get_driver():
    c = st.secrets["neo4j"]

    driver = GraphDatabase.driver(
        c["uri"],
        auth=(c["username"], c["password"])
    )

    driver.verify_connectivity()
    return driver


def query(c, p=None, w=False):
    records, _, _ = get_driver().execute_query(
        c,
        parameters_=p or {},
        database_=st.secrets["neo4j"].get("database", "neo4j"),
        routing_=RoutingControl.WRITE if w else RoutingControl.READ
    )

    return [x.data() for x in records]


def setup_data():

    # -----------------------------
    # Constraints
    # -----------------------------
    query(
        """
        CREATE CONSTRAINT user_name_unique
        IF NOT EXISTS
        FOR (n:User)
        REQUIRE n.name IS UNIQUE
        """,
        w=True
    )

    query(
        """
        CREATE CONSTRAINT motorcycle_name_unique
        IF NOT EXISTS
        FOR (n:Motorcycle)
        REQUIRE n.name IS UNIQUE
        """,
        w=True
    )

    # -----------------------------
    # Users
    # -----------------------------
    query(
        """
        UNWIND $x AS n
        MERGE (:User {name:n})
        """,
        {"x": DATA["users"]},
        True
    )

    # -----------------------------
    # Motorcycles
    # -----------------------------
    query(
        """
        UNWIND $x AS x

        MERGE (m:Motorcycle {name:x.name})

        SET
            m.image_url = coalesce(m.image_url, x.image_url),
            m.image_data = coalesce(m.image_data, x.image_data),
            m.price = coalesce(m.price, 0)
        """,
        {"x": DATA["motorcycles"]},
        True
    )

    # -----------------------------
    # Orders / selections
    # -----------------------------
    query(
        """
        UNWIND $x AS x

        MATCH (u:User {name:x.user})
        MATCH (m:Motorcycle {name:x.motorcycle})

        MERGE (u)-[r:ORDERED]->(m)

        ON CREATE SET
            r.ordered_at = date('2026-09-01')
        """,
        {"x": DATA["likes"]},
        True
    )

    # -----------------------------
    # Generate friendships
    # -----------------------------
    query(
        """
        MATCH (a:User)-[:ORDERED]->(m)<-[:ORDERED]-(b:User)

        WHERE a.name < b.name

        WITH
            a,
            b,
            count(DISTINCT m) AS shared_motorcycles

        WHERE shared_motorcycles > 0

        MERGE (a)-[:FRIEND]->(b)
        """,
        w=True
    )

    # -----------------------------
    # Migrate old relationships
    # -----------------------------
    query(
        """
        MATCH (u:User)-[:LIKES|RENTED]->(m:Motorcycle)

        MERGE (u)-[:ORDERED]->(m)
        """,
        w=True
    )


def users():
    return [
        x["name"]
        for x in query(
            """
            MATCH (u:User)
            RETURN u.name AS name
            ORDER BY name
            """
        )
    ]


def motorcycles():
    return query(
        """
        MATCH (m:Motorcycle)

        RETURN
            m.name AS name,
            m.price AS price,
            m.image_url AS image_url,
            m.image_data AS image_data

        ORDER BY name
        """
    )


def friends(u):
    return [
        x["name"]
        for x in query(
            """
            MATCH (:User {name:$u})-[:FRIEND]-(f:User)

            RETURN DISTINCT
                f.name AS name

            ORDER BY name
            """,
            {"u": u}
        )
    ]


def stats():

    result = query(
        """
        MATCH (u:User)
        WITH count(u) AS users

        MATCH (m:Motorcycle)
        WITH users, count(m) AS motorcycles

        OPTIONAL MATCH (:User)-[f:FRIEND]-(:User)

        WITH
            users,
            motorcycles,
            count(f) / 2 AS friendships

        OPTIONAL MATCH (:User)-[o:ORDERED]->(:Motorcycle)

        RETURN
            users,
            motorcycles,
            friendships,
            count(o) AS orders
        """
    )

    if result:
        return result[0]

    return {
        "users": 0,
        "motorcycles": 0,
        "friendships": 0,
        "orders": 0
    }


def recommendations(u):

    return query(
        """
        MATCH (me:User {name:$u})
              -[:FRIEND]-
              (f:User)
              -[:ORDERED]->
              (m:Motorcycle)

        WHERE NOT EXISTS {
            MATCH (me)-[:ORDERED]->(m)
        }

        WITH
            m,
            collect(DISTINCT f.name) AS friend_names,
            count(DISTINCT f) AS score

        RETURN
            m.name AS name,
            m.price AS price,
            m.image_url AS image_url,
            m.image_data AS image_data,
            friend_names,
            score

        ORDER BY
            score DESC,
            m.name
        """,
        {"u": u}
    )


def add_user(n):

    n = n.strip()

    if n:
        query(
            """
            MERGE (:User {name:$n})
            """,
            {"n": n},
            True
        )


def add_friend(a, b):

    if a != b:
        query(
            """
            MATCH (a:User {name:$a})
            MATCH (b:User {name:$b})

            MERGE (a)-[:FRIEND]->(b)
            """,
            {
                "a": a,
                "b": b
            },
            True
        )


def remove_friend(a, b):

    query(
        """
        MATCH (a:User {name:$a})
              -[r:FRIEND]-
              (b:User {name:$b})

        DELETE r
        """,
        {
            "a": a,
            "b": b
        },
        True
    )


def delete_user(n):

    query(
        """
        MATCH (u:User {name:$n})
        DETACH DELETE u
        """,
        {"n": n},
        True
    )


def add_motorcycle(n, price=0, url="", data=""):

    n = n.strip()

    if n:
        query(
            """
            MERGE (m:Motorcycle {name:$n})

            SET
                m.price = $price,
                m.image_url = $url,
                m.image_data = $data
            """,
            {
                "n": n,
                "price": float(price),
                "url": url,
                "data": data
            },
            True
        )


def delete_motorcycle(n):

    query(
        """
        MATCH (m:Motorcycle {name:$n})
        DETACH DELETE m
        """,
        {"n": n},
        True
    )


def order(u, n):

    query(
        """
        MATCH (u:User {name:$u})
        MATCH (m:Motorcycle {name:$n})

        MERGE (u)-[r:ORDERED]->(m)

        SET r.ordered_at = date()
        """,
        {
            "u": u,
            "n": n
        },
        True
    )


def remove_order(u, n):

    query(
        """
        MATCH (:User {name:$u})
              -[r:ORDERED]->
              (:Motorcycle {name:$n})

        DELETE r
        """,
        {
            "u": u,
            "n": n
        },
        True
    )


def ordered(u):

    return query(
        """
        MATCH (:User {name:$u})
              -[r:ORDERED]->
              (m:Motorcycle)

        RETURN
            m.name AS name,
            m.price AS price

        ORDER BY name
        """,
        {"u": u}
    )


def edges(person=None, show_orders=True):

    p = {"u": person} if person else {}

    if person:
        users_clause = "MATCH (u:User {name:$u})"
    else:
        users_clause = "MATCH (u:User)"

    fs = query(
        users_clause
        + """
        MATCH (u)-[:FRIEND]-(f:User)

        RETURN DISTINCT
            u.name AS a,
            f.name AS b
        """,
        p
    )

    if show_orders:
        os = query(
            users_clause
            + """
            MATCH (u)-[:ORDERED]->(m:Motorcycle)

            RETURN
                u.name AS a,
                m.name AS b
            """,
            p
        )
    else:
        os = []

    return fs, os