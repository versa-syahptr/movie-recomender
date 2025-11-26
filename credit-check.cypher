MATCH (m:Movie {id: $id})
WITH m

OPTIONAL MATCH (cast:Person) -[:CASTED_IN]-> (m)
WITH m, count(cast) as cast_count

OPTIONAL MATCH (crew:Person) -[:WORKED_IN]-> (m)
WITH m, cast_count, count(crew) as crew_count

RETURN
    cast_count = $cast_len AND
    crew_count = $crew_len as complete