MATCH (me:User {name:$user})-[:RENTED]->(shared:Motorcycle)<-[:RENTED]-(other:User)-[:RENTED]->(rec:Motorcycle)
WHERE other <> me AND other.name IN $users AND shared.name IN $models AND rec.name IN $models
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
ORDER BY score DESC, name ASC LIMIT $limit;
