MATCH (me:User {name:$user})-[:RENTED]->(shared:Motorcycle)<-[:RENTED]-(other:User)-[:RENTED]->(rec:Motorcycle)
WHERE me <> other AND NOT EXISTS { (me)-[:RENTED]->(rec) }
WITH DISTINCT shared,other,rec
RETURN rec.name AS motorcycle, count(*) AS score
ORDER BY score DESC, motorcycle ASC;
