import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
import httpx
from pydantic import BaseModel

app = FastAPI(title="Movie Night — API Consumer Service")

# Récupération de la clé TMDB depuis les variables d'environnement Docker
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Mapping temporaire des humeurs vers des IDs de genres TMDB (Exemples)
GENRE_MAP = {
    "chill": 28,     # Action / Aventure soft
    "scary": 27,     # Horreur
    "laugh": 35,     # Comédie
    "cry": 18,       # Drame
    "action": 28     # Action
}

# --- MODELES PYDANTIC POUR LE CONTRAT INTERNE ---
class MovieMinimal(BaseModel):
    id: int
    title: str
    poster_path: Optional[str]
    release_date: Optional[str]

class MovieDetailed(BaseModel):
    id: int
    title: str
    overview: Optional[str]
    duration: Optional[int]
    poster_path: Optional[str]
    genres: List[str]
    casting: List[str]

# --- ENDPOINTS ---

@app.get("/fetch-movies-by-genre", response_model=List[MovieMinimal])
async def fetch_movies_by_genre(mood: str):
    """Appelé par Business Logic pour obtenir des films selon l'humeur"""
    genre_id = GENRE_MAP.get(mood.lower())
    if not genre_id:
        raise HTTPException(status_code=400, detail=f"Humeur '{mood}' non supportée.")

    async with httpx.AsyncClient() as client:
        url = f"{TMDB_BASE_URL}/discover/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "language": "fr-FR"
        }
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erreur lors de la communication avec TMDB")
            
        results = response.json().get("results", [])
        
        # Formatage selon la structure attendue
        movies = []
        for item in results:
            movies.append(MovieMinimal(
                id=item["id"],
                title=item["title"],
                poster_path=item.get("poster_path"),
                release_date=item.get("release_date")
            ))
        return movies

@app.get("/fetch-catalog", response_model=dict)
async def fetch_catalog(page: int = 1, limit: int = 20):
    """Récupère les films populaires pour le catalogue général"""
    async with httpx.AsyncClient() as client:
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {
            "api_key": TMDB_API_KEY,
            "page": page,
            "language": "fr-FR"
        }
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Impossible de joindre le catalogue distant")
            
        json_data = response.json()
        results = json_data.get("results", [])[:limit] # Gestion de la limite simplifiée
        
        movies = [
            MovieMinimal(
                id=item["id"],
                title=item["title"],
                poster_path=item.get("poster_path"),
                release_date=item.get("release_date")
            ) for item in results
        ]
        
        return {
            "total_results": json_data.get("total_results", 0),
            "data": movies
        }

@app.get("/fetch-movie/{movie_id}", response_model=MovieDetailed)
async def fetch_movie_details(movie_id: int):
    """Récupère les détails et les crédits (casting) d'un film"""
    async with httpx.AsyncClient() as client:
        # 1. Requête pour les détails
        detail_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {"api_key": TMDB_API_KEY, "language": "fr-FR"}
        
        # 2. Requête pour le casting (append_to_response optimise l'appel)
        params["append_to_response"] = "credits"
        
        response = await client.get(detail_url, params=params)
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Film inconnu sur TMDB")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erreur interne TMDB")
            
        data = response.json()
        
        # Extraction du casting (Top 5 acteurs)
        cast_list = data.get("credits", {}).get("cast", [])
        top_cast = [actor["name"] for actor in cast_list[:5]]
        
        # Extraction des noms de genres
        genres_list = [g["name"] for g in data.get("genres", [])]

        return MovieDetailed(
            id=data["id"],
            title=data["title"],
            overview=data.get("overview"),
            duration=data.get("runtime"),
            poster_path=data.get("poster_path"),
            genres=genres_list,
            casting=top_cast
        )

@app.get("/search-movies", response_model=List[MovieMinimal])
async def search_movies(query: str):
    """Recherche textuelle sur TMDB"""
    async with httpx.AsyncClient() as client:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "fr-FR"
        }
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erreur lors de la recherche")
            
        results = response.json().get("results", [])
        return [
            MovieMinimal(
                id=item["id"],
                title=item["title"],
                poster_path=item.get("poster_path"),
                release_date=item.get("release_date")
            ) for item in results
        ]