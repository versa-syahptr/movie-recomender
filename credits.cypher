MERGE (m:Movie {id: $movie_id})

with m, $cast AS cast
UNWIND cast AS c
    MERGE (p:Person {id: c.id})
    ON CREATE SET 
        p.name = c.name,
        p.gender = c.gender

    MERGE (p)-[casted:CASTED_IN {credit_id: c.credit_id}]->(m)
    ON CREATE SET 
        casted.character = c.character

WITH m, $crew AS crew
UNWIND crew AS cr
    MERGE (p1:Person {id: cr.id})
    ON CREATE SET 
        p1.name = cr.name,
        p1.gender = cr.gender
    
    MERGE (p1)-[work:WORKED_IN {credit_id: cr.credit_id}]->(m)
    ON CREATE SET
        work.department = cr.department,
        work.job = cr.job
        
RETURN m