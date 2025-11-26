MATCH (m:Movie {id: $id})
WITH m

OPTIONAL MATCH (m)-[:HAS_GENRE]->(g:Genre)
WITH m, count(g) AS genre_count

OPTIONAL MATCH (m)-[:PRODUCED_BY]->(pc:Company)
WITH m, genre_count, count(pc) AS pc_count

OPTIONAL MATCH (m)-[:PRODUCED_IN]->(c:ProductionCountry)
WITH m, genre_count, pc_count, count(c) AS country_count

OPTIONAL MATCH (m)-[:SPOKEN_IN]->(l:Language)
WITH m, genre_count, pc_count, country_count, count(l) AS lang_count

OPTIONAL MATCH (m)-[:HAS_KEYWORD]->(k:Keyword)
WITH m, genre_count, pc_count, country_count, lang_count, count(k) AS keyword_count

RETURN
    genre_count = $genre_len AND
    pc_count = $pc_len AND
    country_count = $country_len AND
    lang_count = $lang_len AND
    keyword_count = $keyword_len AS complete