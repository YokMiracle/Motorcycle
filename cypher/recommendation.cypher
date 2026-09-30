MATCH (me:User {name:$user})-[:LIKES]->(:Motorcycle)<-[:LIKES]-(other:User)-[:LIKES]->(rec:Motorcycle)
WHERE other <> me AND NOT EXISTS { (me)-[:LIKES]->(rec) }
RETURN rec.name AS motorcycle, rec.image_url AS image_url, count(*) AS score
ORDER BY score DESC, motorcycle ASC;
