import json
import pandas as pd
from neo4j import GraphDatabase
from dotenv import dotenv_values, load_dotenv
from argparse import ArgumentParser
from tqdm import tqdm
from typing import Tuple
import os
import requests

load_dotenv()  # Load environment variables from .env file
TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
TMDB_API_URL = "https://api.themoviedb.org/3"


def fetch_movie_details(movie_id: int) -> dict:
    url = f"{TMDB_API_URL}/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching movie ID {movie_id}: {response.status_code}")
        return {}   


def parse_json_columns(frame: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    frame = frame.copy()
    json_col = [col for col in frame.columns if frame[col].apply(lambda x: isinstance(x, str) and x.startswith('[') and x.endswith(']')).all()]
    if not json_col:
        print("No JSON columns found.")

    for col in json_col:
        frame[col] = frame[col].apply(json.loads)
    
    return frame, json_col


def import_movies(session):
    print("=== PIPELINE: Importing Movies ===")
    movies_df = pd.read_csv('tmdb_5000_movies.csv', parse_dates=["release_date"])
    movies_df, json_columns = parse_json_columns(movies_df)
    print(f"JSON columns from movies_df: {json_columns}")
    movie_query = open('movies.cypher').read()
    movie_check_query = open('movie-check.cypher').read()
    for idx, row in tqdm(movies_df.iterrows(), total=movies_df.shape[0], desc="Importing Movies"):
        movie_data = row.to_dict()

        check_params = {
                    "id": movie_data["id"],
                    "genre_len": len(movie_data["genres"]),
                    "pc_len": len(movie_data["production_companies"]),
                    "country_len": len(movie_data["production_countries"]),
                    "lang_len": len(movie_data["spoken_languages"]),
                    "keyword_len": len(movie_data["keywords"]),
                }

        check_result = session.run(movie_check_query, check_params).single()
        if check_result["complete"]:
            continue # skip row

        session.run(movie_query, movie_data)
    print("Movie import completed.")
    return movies_df["id"].tolist()


def import_credits(session):
    print("=== PIPELINE: Importing Credits ===")
    credits_df = pd.read_csv('tmdb_5000_credits.csv')
    credits_df, json_columns_credits = parse_json_columns(credits_df)
    print(f"JSON columns from credits_df: {json_columns_credits}")

    credit_query = open('credits.cypher').read()
    credit_check_query = open('credit-check.cypher').read()
    for idx, row in tqdm(credits_df.iterrows(), total=credits_df.shape[0], desc="Importing Credits"):
        credit_data = row.to_dict()

        credit_check_params = {
                    "id": credit_data["movie_id"],
                    "cast_len": len(credit_data["cast"]),
                    "crew_len": len(credit_data["crew"]),
                }

        check_result = session.run(credit_check_query, credit_check_params).single()
        if check_result["complete"]:
            continue # skip row

        session.run(credit_query, credit_data)
    print("Credit import completed.")

def import_posters(movie_ids, session):
    print("=== PIPELINE: Importing Posters ===")
    for movie_id in tqdm(movie_ids, desc="Fetching Posters"):
        poster_check = session.run("MATCH (m:Movie {id: $id}) RETURN m.poster_url AS poster_url", {"id": movie_id}).single()
        if poster_check and poster_check["poster_url"]:
            continue  # Skip if poster_url already exists

        details = fetch_movie_details(movie_id)
        poster_path = details.get("poster_path")
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            session.run(
                    "MATCH (m:Movie {id: $id}) SET m.poster_url = $poster_url",
                    {"id": movie_id, "poster_url": poster_url}
                )
    print("Poster import completed.")


def fetch_collections(session, movie_ids):
    print("\n=== PIPELINE: Fetching Collections ===")
    for movie_id in tqdm(movie_ids, desc="Fetching Collections"):
        # Skip if Movie already has collection
        rel_check = session.run("""
            MATCH (m:Movie {id: $id})-[:BELONGS_TO]->(:Collection)
            RETURN 1 AS exists
        """, {"id": movie_id}).single()

        if rel_check and rel_check["exists"]:
            continue

        details = fetch_movie_details(movie_id)
        if not details:
            continue

        belongs = details.get("belongs_to_collection")
        if not belongs:
            continue  # Movie has no collection

        cq = """
            MERGE (c:Collection {id: $cid})
            SET c.name = $cname
            WITH c
            MATCH (m:Movie {id: $mid})
            MERGE (m)-[:BELONGS_TO]->(c)
        """
        session.run(cq, {
            "cid": belongs["id"],
            "cname": belongs["name"],
            "mid": movie_id
        })


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('config', type=str, help='Path to Neo4j config file')
    parser.add_argument("--movies", action="store_true")
    parser.add_argument("--credits", action="store_true")
    parser.add_argument("--posters", action="store_true")
    parser.add_argument("--collections", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    is_default = not (args.movies or args.credits or args.posters or args.collections or args.all)

    config = dotenv_values(args.config) # Load Neo4j credentials
    driver = GraphDatabase.driver(config["NEO4J_URI"], auth=(config["NEO4J_USERNAME"], config["NEO4J_PASSWORD"]))


    with driver.session() as session:
        movie_ids = []
        if args.movies or args.all or is_default:
            movie_ids = import_movies(session)
        if args.credits or args.all or is_default:
            import_credits(session)
        if args.posters or args.all or is_default:
            if not movie_ids:
                result = session.run("MATCH (m:Movie) RETURN m.id AS id")
                movie_ids = [record["id"] for record in result]
            import_posters(movie_ids, session)
        if args.collections or args.all or is_default:
            if not movie_ids:
                result = session.run("MATCH (m:Movie) RETURN m.id AS id")
                movie_ids = [record["id"] for record in result]
            fetch_collections(session, movie_ids)

    
    print("Data import completed.")
    driver.close()



