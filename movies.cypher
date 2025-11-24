MERGE (m:Movie {id: $id})
ON CREATE SET
    m.title = $title,
    m.homepage = $homepage,
    m.budget = $budget,
    m.popularity = $popularity,
    m.original_language = $original_language,
    m.overview = $overview,
    m.original_title = $original_title,
    m.release_date = $release_date,
    m.revenue = $revenue,
    m.status = $status,
    m.tagline = $tagline,
    m.vote_average = $vote_average,
    m.vote_count = $vote_count

WITH m, $genres AS genres
UNWIND genres AS g
    MERGE (genre:Genre {id: g.id})
    ON CREATE SET genre.name = g.name
    MERGE (m)-[:HAS_GENRE]->(genre)

WITH m, $production_companies AS production_companies
UNWIND production_companies AS pc
    MERGE (company:Company {id: pc.id})
    ON CREATE SET company.name = pc.name
    MERGE (m)-[:PRODUCED_BY]->(company)

WITH m, $production_countries AS production_countries
UNWIND production_countries AS pco
    MERGE (country:ProductionCountry {iso_3166_1: pco.iso_3166_1})
    ON CREATE SET country.name = pco.name
    MERGE (m)-[:PRODUCED_IN]->(country)

WITH m, $spoken_languages AS spoken_languages
UNWIND spoken_languages AS sl
    MERGE (language:Language {iso_639_1: sl.iso_639_1})
    ON CREATE SET language.name = sl.name
    MERGE (m)-[:SPOKEN_IN]->(language)

WITH m, $keywords AS keywords
UNWIND keywords AS kw
    MERGE (keyword:Keyword {id: kw.id})
    ON CREATE SET keyword.name = kw.name
    MERGE (m)-[:HAS_KEYWORD]->(keyword)

RETURN m