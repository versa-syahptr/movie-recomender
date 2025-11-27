import streamlit as st
from typing import List, Dict, Any
from neo4j import GraphDatabase
from datetime import date
import atexit
from dotenv import dotenv_values


## DATA FUNCTION

def get_image_url(poster_url: str) -> str:
    if poster_url:
        return poster_url
    return "https://critics.io/img/movies/poster-placeholder.png"


@st.cache_resource
def create_driver():
    config_fallback = dotenv_values("Neo4j Aura Created Nov 24 2025.txt")
    uri = st.secrets.get("NEO4J_URI", config_fallback.get("NEO4J_URI"))
    username = st.secrets.get("NEO4J_USERNAME", config_fallback.get("NEO4J_USERNAME"))
    password = st.secrets.get("NEO4J_PASSWORD", config_fallback.get("NEO4J_PASSWORD"))
    return GraphDatabase.driver(uri, auth=(username, password))

driver = create_driver()
atexit.register(driver.close)

@st.cache_data(ttl=600)
def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params)
        return result.data()
    
def run_query_no_cache(query, params=None):
    with driver.session() as session:
        result = session.run(query, params)
        return result.data()

@st.cache_data(ttl=600)
def get_movie_details(movie_id):
    query = """
            MATCH (m:Movie {id: $movie_id}) 
            OPTIONAL MATCH (p:Person) -[cast:CASTED_IN]-> (m) LIMIT 5
            OPTIONAL MATCH (m) -[]-> (g:Genre)
            OPTIONAL MATCH (m) -[]-> (comp:Company)
            OPTIONAL MATCH (m) -[]-> (l:Language)
            OPTIONAL MATCH (m) -[]-> (k:Keyword)
            OPTIONAL MATCH (m) -[]-> (pc:ProductionCountry)
            OPTIONAL MATCH (director:Person) -[crew:WORKED_IN {job: "Director"}]-> (m)
            RETURN m.id AS id, m.title AS title, 
                m.overview AS overview, 
                m.poster_url AS poster_url, 
                m.vote_average AS rating,
                date(m.release_date) as release_date,
                COLLECT(DISTINCT g.name) AS genres,
                COLLECT(DISTINCT comp.name) as companies,
                COLLECT(DISTINCT l.name) as languages,
                COLLECT(DISTINCT k.name) as keywords,
                COLLECT(DISTINCT pc.name) as countries,
                COLLECT(DISTINCT p.name) as casts,
                COLLECT(DISTINCT director.name) AS director
            LIMIT 1
            """
    return run_query(query, {"movie_id": movie_id})[0]

@st.cache_data(ttl=60)
def get_random_movies(limit: int =10) -> List[Dict[str, Any]]:
    query = """
    MATCH (m:Movie)
    RETURN m.id AS id, m.title AS title, m.poster_url AS poster_url, m.release_date.year AS release_year
    ORDER BY rand()
    LIMIT $limit
    """
    return run_query_no_cache(query, {"limit": limit})


def watch_movie(movie: Dict[str, Any]):
    user = st.session_state.get("selected_user")
    if not user:
        st.error("No user selected.")
        return
    if movie["id"] in st.session_state.get("watch_history", []):
        st.toast(f"You have already watched {movie['title']}.", icon="ℹ️")
        return
    query = """
            MATCH (u:User {id: $user_id}), (m:Movie {id: $movie_id})
            MERGE (u)-[:WATCHED {watched_at: datetime()}]->(m)
            """
    run_query(query, {"user_id": user["id"], "movie_id": movie["id"]})
    st.session_state["watch_history"].append(movie["id"])
    st.toast(f"{movie['title']} marked as watched!", icon="✅")


def get_user_watch_history(user_id: str) -> List[str]:
    query = """
            MATCH (u:User {id: $user_id}) -[a:WATCHED]-> (m:Movie)
            RETURN COLLECT(DISTINCT m.id) as watchlist
            """
    result = run_query_no_cache(query, {"user_id": user_id})
    if result:
        return result[0]["watchlist"]
    return []

## ELEMENT or SECTION FUNCTION

@st.dialog(title="Movie Details")
def page_details(movie: Dict[str, Any]):
    with st.spinner("Loading movie details..."):
        movie = get_movie_details(movie["id"])
    st.title(movie["title"])
    left, right = st.columns([3, 1])
    left.image(get_image_url(movie["poster_url"]), width=300)
    with right.container():
        with st.container(horizontal=True):
            st.markdown(f"**Released:** {movie.get("release_date", date(1,1,1)).strftime("%d/%m/%Y")}")
            # st.write()
            st.markdown(f"⭐ ({movie.get("rating", 0)}/10)")
        watched = movie['id'] in st.session_state.get("watch_history", [])
        if st.button("Watch", icon=":material/play_arrow:" if not watched else ":material/check_circle:", 
                    key=f"watch_{movie['id']}", help="Watch Movie" if not watched else "Already Watched"):
            watched = True
            watch_movie(movie)

    st.markdown("### Overview")
    st.write(movie["overview"])

    st.markdown(f"**Genres:** {', '.join(movie['genres'])}")
    st.markdown(f"**Production Companies:** {', '.join(movie['companies'])}")
    st.markdown(f"**Languages:** {', '.join(movie['languages'])}")
    st.markdown(f"**Keywords:** {', '.join(movie['keywords'])}")
    st.markdown(f"**Production Countries:** {', '.join(movie['countries'])}")
    st.markdown(f"**Directed by:** {', '.join(movie['director'])}")
    st.markdown(f"**Cast:** {', '.join(movie['casts'])}")


def movie_list_section(title: str, movie_subset: List[Dict[str, Any]], show_refresh_button: bool = False, refresh_action: callable = None): 
    """
    Shows a list of movies with their posters, titles, and release years.
    
    :param title: Section title
    :param movie_subset: List of movies to display, each as a dictionary with keys 'id', 'title', 'poster_url', and 'release_year'
    """
    with st.container(horizontal=True, horizontal_alignment="left"):
        st.subheader(title)
        if show_refresh_button:
            st.button("", icon=":material/refresh:", key=f"refresh_{title}", on_click=refresh_action, help="Refresh Movie List")
    with st.container(horizontal=True, vertical_alignment="distribute", horizontal_alignment="center"):
        for movie in movie_subset:
            with st.container(vertical_alignment="distribute", horizontal_alignment="center", gap="small"):
                st.image(get_image_url(movie["poster_url"]), width=150)
                st.markdown(f"**{movie['title']}**", width="content")
                st.caption(f"{movie['release_year']}", width="content")
                if st.button(
                    "Show Details",
                    help=movie["title"],
                ):
                    page_details(movie)

# --------------------- HOME PAGE ---------------------
st.set_page_config(layout="wide")
st.title("🎬 Streamflix Movies")

random_movies = get_random_movies()

movie_list_section("Random Movies", random_movies, show_refresh_button=True, refresh_action=lambda: get_random_movies.clear() and st.rerun())

consistent_movie_query = """
MATCH (m:Movie)
RETURN m.id AS id, m.title AS title, m.poster_url AS poster_url, m.release_date.year AS release_year
LIMIT 10
"""

consistent_movies = run_query(consistent_movie_query)
movie_list_section("Movies", consistent_movies)

# for user account selection
with st.sidebar:
    users = run_query("MATCH (u:User) RETURN u.id AS id, u.name AS name")
    selected_user = st.radio("Choose User Account",
                             options=users,
                             format_func=lambda user: user["name"],
                             index=None,
                             key="user_account")
    
    if selected_user:
        st.write(f"Logged in as **_{selected_user['name']}_** `id: {selected_user['id']}`")
    
        st.session_state["selected_user"] = selected_user
        history = run_query("""
                            MATCH (u:User {id: $user_id}) -[a:WATCHED]-> (m:Movie)
                            RETURN COLLECT(DISTINCT m.id) as watchlist
                            """, {"user_id": selected_user["id"]})[0]["watchlist"]
        st.session_state["watch_history"] = history
    else:
        st.session_state["selected_user"] = None
        st.session_state["watch_history"] = []
        st.warning("Please select a user account to track your watch history.")

    st.markdown("---")
    