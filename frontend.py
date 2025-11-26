import streamlit as st
from neo4j import GraphDatabase
from dotenv import dotenv_values

config = dotenv_values("Neo4j Aura Created Nov 24 2025.txt") # Load Neo4j credentials
driver = GraphDatabase.driver(config["NEO4J_URI"], auth=(config["NEO4J_USERNAME"], config["NEO4J_PASSWORD"]))


@st.cache_data(ttl=600) # 10 minutes cache
def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params)
        return [record.data() for record in result]

st.set_page_config(layout="wide")

movies = []
movie_query = """
MATCH (m:Movie)
RETURN m.id AS id, m.title AS title, m.overview AS overview, m.poster_url AS poster_url
LIMIT 20
"""
results = run_query(movie_query)
for record in results:
    movies.append(
        {
            "id": record["id"],
            "title": record["title"],
            "overview": record["overview"],
            "poster": record["poster_url"],
        }
    )

# --- Page State ---
if "page" not in st.session_state:
    st.session_state.page = "home"

if "movie_selected" not in st.session_state:
    st.session_state.movie_selected = None


# --------------------- HOME PAGE ---------------------
def page_home():

    st.title("🎬 Streamflix Movies")

    st.subheader("Trending Now")

    with st.container(horizontal=True):

        for movie in movies:
            # each poster-building block
            with st.container():
                st.image(movie["poster"], width=160)
                st.caption(movie["title"])
                if st.button(
                    "Show Details",
                    key=f"poster_{movie['id']}",
                    help=movie["title"],
                ):
                    st.session_state.movie_selected = movie
                    st.session_state.page = "details"
                    st.rerun()




# --------------------- DETAILS PAGE ---------------------
def page_details():

    movie = st.session_state.movie_selected

    if movie is None:
        st.session_state.page = "home"
        st.rerun()

    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()

    st.title(movie["title"])
    st.image(movie["poster"], width=300)

    st.markdown("### Overview")
    st.write(movie["overview"])


# --------------------- Render Correct Page ---------------------
if st.session_state.page == "home":
    page_home()
else:
    page_details()