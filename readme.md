# 🎬 NeoStreamFlix - Movie Recommendation System


A Streamlit-based movie recommendation application powered by Neo4j graph database. This application provides personalized movie recommendations based on various criteria including keywords, genres, cast, directors, and collaborative filtering.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [1. Python Environment Setup](#1-python-environment-setup)
  - [2. Database Connection](#2-database-connection)
  - [3. Installing Dependencies](#3-installing-dependencies)
  - [4. Running the Streamlit App](#4-running-the-streamlit-app)
- [Testing the Application](#testing-the-application)
- [Project Structure](#project-structure)
- [Data Files](#data-files)

## Features

- **Random Movie Browsing**: View random movies with refresh functionality
- **Popular Movies**: Discover trending movies sorted by popularity
- **Smart Recommendations**: Get recommendations based on:
  - Keywords
  - Genres
  - Production Companies
  - Cast/Actors
  - Directors
  - Languages
  - Production Countries
- **Watch History**: Track movies you've watched
- **Collaborative Filtering**: Get recommendations based on similar users' preferences
- **Collection-based Recommendations**: Discover movies from collections you've watched

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Neo4j Aura** or **Neo4j Local Instance** running
- Git (for version control)
- A terminal/command line interface


## Setup Instructions

### 1. Python Environment Setup

#### Option A: Using venv (Recommended)

```bash
# Navigate to the project directory
cd /path/to/movie-recomender

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

#### Option B: Using conda

```bash
# Create a conda environment
conda create -n streamflix python=3.10

# Activate the environment
conda activate streamflix
```

### 2. Database Connection

#### Step 1: Prepare Neo4j Credentials

You need to have your Neo4j connection details. Create a `.streamlit/secrets.toml` file in the project root:

```bash
# Create the .streamlit directory if it doesn't exist
mkdir -p .streamlit

# Create the secrets.toml file
touch .streamlit/secrets.toml
```

Then add your Neo4j credentials to `.streamlit/secrets.toml`:

For **Neo4j Aura**:
```toml
NEO4J_URI = "bolt://your-uri:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your-password"
```

For **Local Neo4j installations**:
```toml
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your-password"
```


#### Step 2: Verify Database Connection

```bash
# Test the connection by running Python
python3

# In Python interpreter:
from neo4j import GraphDatabase

uri = "bolt://your-uri:7687"
auth = ("neo4j", "your-password")
driver = GraphDatabase.driver(uri, auth=auth)

# Test connection
with driver.session() as session:
    result = session.run("RETURN 1")
    print(result.single())

driver.close()
```

### 3. Installing Dependencies

```bash
# Ensure your virtual environment is activated
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install required packages
pip install -r requirements.txt
```

**Requirements include:**
- `streamlit` - Web app framework
- `neo4j` - Neo4j driver for Python
- `python-dotenv` - Environment variable management
- `pandas` - Data manipulation
- `requests` - HTTP requests (optional)
- `tqdm` - Progress bars (optional)

Verify installation:

```bash
pip list
```

### 4. Running the Streamlit App

```bash
# Ensure you're in the project directory with venv activated
cd /path/to/project/movie-recomender
source .venv/bin/activate

# Run the Streamlit app
streamlit run frontend.py
```

The app will start and open in your default browser at `http://localhost:8501`

If it doesn't open automatically, manually navigate to the URL shown in the terminal.

## Testing the Application

### Basic Functionality Tests

#### 1. **User Account Selection**
- [ ] Open the sidebar and select a user account
- [ ] Check that watch history and recommendations appear

#### 2. **Random Movies Section**
- [ ] Verify random movies display with posters, titles, and release years
- [ ] Click the refresh button (⟳) and confirm new movies appear
- [ ] Verify the cache is skipped on refresh (different movies should appear)

#### 3. **Popular Movies Section**
- [ ] Verify popular movies display sorted by popularity
- [ ] Confirm movies are the same across page refreshes (cached)

#### 4. **Movie Details Modal**
- [ ] Click "Show Details" on any movie
- [ ] Verify the modal displays:
  - Movie poster
  - Release date
  - Rating and popularity
  - Overview
  - Genres, companies, languages, keywords, countries
  - Director and cast information

#### 5. **Watch History**
- [ ] Select a user account
- [ ] Click "Watch" on a movie in the details modal
- [ ] Verify toast notification appears
- [ ] Check that the movie appears in "Watch History" section
- [ ] Try watching the same movie again and verify the duplicate warning

#### 6. **Recommendations**
- [ ] Click "Get Recommendation" on any movie
- [ ] Verify you're navigated to the recommendations page
- [ ] Check recommendations by:
  - Similar Keywords
  - Similar Genre
  - Same Production Company
  - Shared Cast
  - Same Director
  - Same Language
  - Same Production Country
- [ ] Click the back button (<-) to return to home

#### 7. **Collaborative Filtering**
- [ ] Select a user with watch history
- [ ] Verify "Users with Similar Interests Also Watched" section appears
- [ ] Confirm recommendations are based on similar users' watched movies

#### 8. **Collection-based Recommendations**
- [ ] Verify "Because You Watched Movies in This Collection" section appears
- [ ] Confirm movies are from same collections as watched movies

#### 9. **Recommendation Limit Slider**
- [ ] Adjust the slider in the sidebar (1-50)
- [ ] Verify that recommendations are limited to the selected number

#### 10. **No User Selected**
- [ ] Deselect user account
- [ ] Verify warning message appears
- [ ] Confirm recommendation sections don't display

### Performance Tests

- [ ] Load time for initial page: Should be < 2 seconds
- [ ] Movie details modal: Should load in < 1 second
- [ ] Refresh button: Should show new movies instantly

### Edge Cases

- [ ] Test with user that has no watch history
- [ ] Test with user that has extensive watch history
- [ ] Test recommendation with movie that has minimal connections
- [ ] Test with empty recommendation results
- [ ] Test with special characters in movie titles

## Project Structure

```
movie-recomender/
├── frontend.py                           # Main Streamlit application
├── import.py                             # Data import script
├── requirements.txt                      # Python dependencies
├── readme.md                             # This file
├── Neo4j Aura Created Nov 24 2025.txt    # Neo4j credentials
├── tmdb_5000_movies.csv                  # Movie data
├── tmdb_5000_credits.csv                 # Credits data
├── credit-check.cypher
├── credits.cypher
├── eda.ipynb                             # Exploratory data analysis
├── movie-check.cypher
└── movies.cypher
```

## Data Files

### CSV Files
- **tmdb_5000_movies.csv**: Contains movie metadata (title, genres, release date, popularity, etc.)
- **tmdb_5000_credits.csv**: Contains cast and crew information

### Cypher Scripts
Query scripts for:
- Movie data import
- Credit/cast data import
- Genre relationships
- Data validation checks

## Troubleshooting

### Connection Issues

**Error: "Failed to establish connection"**
- Verify Neo4j URI is correct
- Check username and password
- Ensure Neo4j server is running
- Check firewall settings

### Import Errors

**Error: "No module named 'streamlit'"**
```bash
pip install -r requirements.txt
```

### Cache Issues

**Random movies not changing on refresh:**
- Verify `.clear()` is being called on the cache
- Check that `skip_cache=True` is passed to `run_query_no_cache()`

### Performance Issues

**Slow recommendations:**
- Check Neo4j indexes are created
- Verify database has sufficient memory
- Check network latency to Neo4j server

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Neo4j Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

## License

This project is part of a movie recommendation system demonstration.

---

**Last Updated:** December 2, 2025
