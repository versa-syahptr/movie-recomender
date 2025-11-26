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




if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('config', type=str, help='Path to Neo4j config file')
    args = parser.parse_args()

    config = dotenv_values(args.config) # Load Neo4j credentials
    driver = GraphDatabase.driver(config["NEO4J_URI"], auth=(config["NEO4J_USERNAME"], config["NEO4J_PASSWORD"]))

    movies_df = pd.read_csv('tmdb_5000_movies.csv', parse_dates=["release_date"])
    credits_df = pd.read_csv('tmdb_5000_credits.csv')

    movies_df, json_columns = parse_json_columns(movies_df)
    print(f"JSON columns from movies_df: {json_columns}")

    credits_df, json_columns_credits = parse_json_columns(credits_df)
    print(f"JSON columns from credits_df: {json_columns_credits}")

    movie_query = open('movies.cypher').read()
    credit_query = open('credits.cypher').read()
    movie_check_query = open('movie-check.cypher').read()
    credit_check_query = open('credit-check.cypher').read()

    with driver.session() as session:
        try:
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
            print("Movies imported. Now importing credits...")

        except KeyboardInterrupt:
            print("Movie import interrupted by user. Proceeding to credits import...")
        
        try:
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
            
            print("Credits imported. fetching movie poster URLs...")

        except KeyboardInterrupt:
            print("Credit import interrupted by user. Proceeding to fetch movie poster URLs...")

        for movie_id in tqdm(movies_df["id"], total=movies_df.shape[0], desc="Fetching Posters"):
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
    
    print("Data import completed.")


