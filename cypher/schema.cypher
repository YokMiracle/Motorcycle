CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE;
CREATE CONSTRAINT motorcycle_name_unique IF NOT EXISTS FOR (m:Motorcycle) REQUIRE m.name IS UNIQUE;
