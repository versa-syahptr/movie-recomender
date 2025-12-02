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
                m.popularity AS popularity,
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

@st.cache_data(ttl=600)
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
    st.session_state["watch_history"].append(movie)
    st.toast(f"{movie['title']} marked as watched!", icon="✅")


@st.cache_data(ttl=10)
def get_user_watch_history(user_id: str) -> List[str]:
    if user_id == 0:
        return []
    query = """
            MATCH (u:User {id: $user_id}) -[w:WATCHED]-> (m:Movie)
            RETURN m.id AS id, m.title AS title, m.poster_url AS poster_url, m.release_date.year AS release_year
            ORDER BY w.watched_at DESC
            """
    result = run_query_no_cache(query, {"user_id": user_id})
    if result:
        return result
    return []

# ==========================================================
# =============  Recommendation query calls  ===============
# ==========================================================

class Recommender:
    keyword = """
        MATCH (m:Movie {id: $id})-[:HAS_KEYWORD]->(k:Keyword)
        WITH m, collect(DISTINCT k) AS keywords

        MATCH (rec:Movie)-[hk:HAS_KEYWORD]->(rk:Keyword)
        WHERE rec <> m
        WITH m, rec, keywords, collect(DISTINCT rk) AS recKeywords
        WITH m, rec, size([x IN recKeywords WHERE x IN keywords]) AS commonKeywords
        WHERE commonKeywords > 0
        RETURN rec.id AS id, rec.title AS title, rec.poster_url AS poster_url, rec.release_date.year AS release_year
        LIMIT $limit
    """
    genre = """
        MATCH (m:Movie {title: "Avatar"})-[hg:HAS_GENRE]->(g:Genre)
        WITH m, collect(DISTINCT g) AS genres

        MATCH (rec:Movie)-[hg:HAS_GENRE]->(rg:Genre)
        WHERE rec <> m
        WITH m, rec, genres, collect(DISTINCT rg) AS recGenres
        WITH m, rec, size([x IN recGenres WHERE x IN genres]) AS commonGeneres
        WHERE commonGeneres > 0
        RETURN rec.id AS id, rec.title AS title, rec.poster_url AS poster_url, rec.release_date.year AS release_year
        LIMIT $limit
    """
    company = """
        MATCH (m:Movie {id: $id})-[:PRODUCED_BY]->(c:Company)
        WITH m, collect(DISTINCT c) AS companies

        MATCH (rec:Movie)-[:PRODUCED_BY]->(rc:Company)
        WHERE rec <> m
        WITH m, rec, companies, collect(DISTINCT rc) AS recComp
        WITH m, rec, size([x IN recComp WHERE x IN companies]) AS commonComp
        WHERE commonComp > 0
        RETURN rec.id AS id, rec.title AS title, rec.poster_url AS poster_url, rec.release_date.year AS release_year
        ORDER BY commonComp DESC
        LIMIT $limit
    """
    cast = """
        MATCH (m:Movie {id: $id})<-[:CASTED_IN]-(p:Person)
        WITH m, collect(DISTINCT p) AS people

        MATCH (rec:Movie)<-[:CASTED_IN]-(rp:Person)
        WHERE rec <> m
        WITH m, rec, people, collect(DISTINCT rp) AS recPerson
        WITH m, rec, size([x IN recPerson WHERE x IN people]) AS commonCast
        WHERE commonCast > 0
        RETURN rec.id AS id, rec.title AS title, rec.poster_url AS poster_url, rec.release_date.year AS release_year
        ORDER BY commonCast DESC
        LIMIT $limit
    """
    director = """
        MATCH (m:Movie {id: $id})
        MATCH (p:Person)-[d:WORKED_IN {job: "Director"}]->(m)
        MATCH (p)-[d2:WORKED_IN {job: "Director"}]->(rec:Movie)
        WHERE rec <> m

        RETURN rec.id AS id, rec.title AS title, rec.poster_url AS poster_url, rec.release_date.year AS release_year, p.name as director
        ORDER BY rec.popularity DESC
        LIMIT $limit;
    """

    def __init__(self, movie_id: int, limit: int):
        self.movie_id = movie_id
        self.limit = limit

    def get(self, name):
        q = getattr(self, name)
        return run_query(q, {"id": self.movie_id, "limit": self.limit})

def get_popular_movies(limit=10):
    query = """
            MATCH (m:Movie)
            RETURN m.id AS id, m.title AS title, m.poster_url AS poster_url, m.release_date.year AS release_year
            ORDER BY m.popularity DESC
            LIMIT $limit;
    """
    return run_query(query, {"limit": limit})

def get_colaborative_recommendation(uid, limit=10):
    q = """
        MATCH (u1:User {id: $uid})
        MATCH (u1)-[:WATCHED]->(:Movie)-[:HAS_KEYWORD]->(k:Keyword)
        MATCH (u2:User)-[:WATCHED]->(:Movie)-[:HAS_KEYWORD]->(k)
        WHERE u2 <> u1
        MATCH (u2)-[:WATCHED]->(rec:Movie)
        WHERE NOT (u1)-[:WATCHED]->(rec)

        RETURN rec.id as id, rec.title as title, rec.popularity as popularity, rec.poster_url AS poster_url, 
               rec.release_date.year AS release_year, COUNT(DISTINCT k) AS shared_kwds
        ORDER BY shared_kwds DESC, popularity DESC
        LIMIT $limit;
    """
    return run_query(q, {"uid": uid, "limit": limit})


# ==========================================================
# =============  Widgets & Layout func calls ===============
# ==========================================================

@st.dialog(title="Movie Details", width="medium")
def page_details(movie: Dict[str, Any]):
    with st.spinner("Loading movie details..."):
        movie = get_movie_details(movie["id"])
    st.title(movie["title"])
    left, right = st.columns([4, 2])
    left.image(get_image_url(movie["poster_url"]))
    with right.container():
        with st.container(horizontal=True):
            st.markdown(f"**Released:** {movie.get("release_date", date(1,1,1)).strftime("%d/%m/%Y")}")
            # st.write()
            st.markdown(f"⭐ ({movie.get("rating", 0)}/10)")
            st.markdown(f"**Popularity:** {movie["popularity"]}")
        # history = st.session_state.get("watch_history", [])
        current_user = st.session_state.get("selected_user", {"id":0})
        if current_user:
            history = [m["id"] for m in get_user_watch_history(current_user["id"])]
        else:
            history = []
        watched = movie['id'] in history
        with st.container(horizontal=True):
            if st.button("Watch", icon=":material/play_arrow:" if not watched else ":material/check_circle:", 
                        key=f"watch_{movie['id']}", help="Watch Movie" if not watched else "Already Watched"):
                watched = True
                watch_movie(movie)
            if st.button("Get Recommendation"):
                st.query_params.recommend = movie["id"]
                st.rerun()

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
                    key=f"{title.replace(' ', '_')}_details_{movie["id"]}"
                ):
                    page_details(movie)
        if not movie_subset:
            st.write("EMPTY")

# --------------------- HOME PAGE ---------------------
def home_page():
    
    st.title("🎬 NeoStreamFlix Movies")

    random_movies = get_random_movies()
    movie_list_section("Random Movies", random_movies, show_refresh_button=True, refresh_action=lambda: get_random_movies.clear() and st.rerun())

    popular_movies = get_popular_movies(limit)
    movie_list_section("Popular Movies", popular_movies)

    if (user:=st.session_state.get("selected_user")):
        colab_rec = get_colaborative_recommendation(user["id"], limit)
        movie_list_section(f"Users with Similar Interests Also Watched", colab_rec)
        history = get_user_watch_history(user["id"])
        movie_list_section(f"Watch History for {user["name"]}", history)


st.set_page_config(layout="wide")

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
        history = get_user_watch_history(selected_user["id"])
        st.session_state["watch_history"] = history
    else:
        st.session_state["selected_user"] = None
        st.session_state["watch_history"] = []
        st.warning("Please select a user account to track your watch history.")

    st.markdown("---")
    limit = st.sidebar.slider("Recommendation Limit", min_value=1, max_value=50, value=10)



# Navigation logic
if st.query_params.get("recommend"): # recommendation page
    if st.button("<-"):
        st.query_params.clear()
        st.rerun()
    movie_id = int(st.query_params.recommend)
    movie_title = run_query("MATCH (m:Movie {id: $id}) RETURN m.title as t", {"id": movie_id})[0]['t']
    recommender = Recommender(movie_id, limit)

    # keyword
    movie_list_section(f"Similar Keywords to `{movie_title}`",
                       recommender.get("keyword"))
    # genre
    movie_list_section(f"Similar Genre to `{movie_title}`",
                       recommender.get("genre"))
    # company
    movie_list_section(f"Produced by the same Company as `{movie_title}`",
                       recommender.get("company"))
    # casts
    movie_list_section(f"Shared the same Cast as `{movie_title}`",
                       recommender.get("cast"))
    #director
    recommend_by_director = recommender.get("director")
    director_name = recommend_by_director[0]["director"]
    movie_list_section(f"Also directed by `{director_name}`", recommend_by_director)

    st.stop()

home_page()
