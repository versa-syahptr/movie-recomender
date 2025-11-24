import json
import pandas as pd
from neo4j import GraphDatabase
from dotenv import dotenv_values
from argparse import ArgumentParser
from tqdm import tqdm
from typing import Tuple

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

    with driver.session() as session:
        for idx, row in tqdm(movies_df.iterrows(), total=movies_df.shape[0], desc="Importing Movies"):
            movie_data = row.to_dict()
            session.run(movie_query, movie_data)
        
        print("Movies imported. Now importing credits...")

        for idx, row in tqdm(credits_df.iterrows(), total=credits_df.shape[0], desc="Importing Credits"):
            credit_data = row.to_dict()
            session.run(credit_query, credit_data)
    
    print("Data import completed.")

