import asyncio
import json
import os
import grpc
from grpc import aio
import httpx
import redis.asyncio as aioredis
import api_consumer_pb2
import api_consumer_pb2_grpc

TMDB_API_KEY  = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
REDIS_URL     = os.getenv("REDIS_URL", "redis://redis:6379")

GENRE_MAP = {
    "chill":  28,
    "scary":  27,
    "laugh":  35,
    "cry":    18,
    "action": 28,
}

redis_client: aioredis.Redis = None


class ApiConsumerServicer(api_consumer_pb2_grpc.ApiConsumerServiceServicer):

    async def FetchMoviesByGenre(self, request, context):
        genre_id = GENRE_MAP.get(request.mood.lower())
        if not genre_id:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Humeur '{request.mood}' non supportée.")

        cache_key = f"genre:{request.mood.lower()}"
        cached = await redis_client.get(cache_key)
        if cached:
            return api_consumer_pb2.MovieList(movies=[
                api_consumer_pb2.Movie(**m) for m in json.loads(cached)
            ])

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{TMDB_BASE_URL}/discover/movie", params={
                "api_key":     TMDB_API_KEY,
                "with_genres": genre_id,
                "sort_by":     "popularity.desc",
                "language":    "fr-FR",
            })

        if resp.status_code != 200:
            await context.abort(grpc.StatusCode.INTERNAL, "Erreur lors de la communication avec TMDB")

        movies = [
            {
                "id": item["id"],
                "title": item["title"],
                "poster_path": item.get("poster_path") or "",
                "release_date": item.get("release_date") or "",
            }
            for item in resp.json().get("results", [])
        ]
        await redis_client.setex(cache_key, 1800, json.dumps(movies))  # 30 min

        return api_consumer_pb2.MovieList(movies=[
            api_consumer_pb2.Movie(**m) for m in movies
        ])

    async def FetchCatalog(self, request, context):
        page  = request.page or 1
        limit = request.limit or 20

        cache_key = f"catalog:{page}:{limit}"
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            return api_consumer_pb2.CatalogResponse(
                total_results=data["total_results"],
                movies=[api_consumer_pb2.Movie(**m) for m in data["movies"]],
            )

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{TMDB_BASE_URL}/movie/popular", params={
                "api_key":  TMDB_API_KEY,
                "page":     page,
                "language": "fr-FR",
            })

        if resp.status_code != 200:
            await context.abort(grpc.StatusCode.INTERNAL, "Impossible de joindre le catalogue distant")

        json_data = resp.json()
        movies = [
            {
                "id": item["id"],
                "title": item["title"],
                "poster_path": item.get("poster_path") or "",
                "release_date": item.get("release_date") or "",
            }
            for item in json_data.get("results", [])[:limit]
        ]
        payload = {"total_results": json_data.get("total_results", 0), "movies": movies}
        await redis_client.setex(cache_key, 600, json.dumps(payload))  # 10 min

        return api_consumer_pb2.CatalogResponse(
            total_results=payload["total_results"],
            movies=[api_consumer_pb2.Movie(**m) for m in movies],
        )

    async def FetchMovie(self, request, context):
        cache_key = f"movie:{request.movie_id}"
        cached = await redis_client.get(cache_key)
        if cached:
            return api_consumer_pb2.MovieDetailed(**json.loads(cached))

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{TMDB_BASE_URL}/movie/{request.movie_id}",
                params={
                    "api_key":            TMDB_API_KEY,
                    "language":           "fr-FR",
                    "append_to_response": "credits",
                },
            )

        if resp.status_code == 404:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Film inconnu sur TMDB")
        if resp.status_code != 200:
            await context.abort(grpc.StatusCode.INTERNAL, "Erreur interne TMDB")

        data      = resp.json()
        cast_list = data.get("credits", {}).get("cast", [])
        movie = {
            "id":           data["id"],
            "title":        data["title"],
            "overview":     data.get("overview") or "",
            "duration":     data.get("runtime") or 0,
            "poster_path":  data.get("poster_path") or "",
            "release_date": data.get("release_date") or "",
            "genres":       [g["name"] for g in data.get("genres", [])],
            "casting":      [actor["name"] for actor in cast_list[:5]],
        }
        await redis_client.setex(cache_key, 3600, json.dumps(movie))  # 1h

        return api_consumer_pb2.MovieDetailed(**movie)

    async def SearchMovies(self, request, context):
        cache_key = f"search:{request.query.lower().strip()}"
        cached = await redis_client.get(cache_key)
        if cached:
            return api_consumer_pb2.MovieList(movies=[
                api_consumer_pb2.Movie(**m) for m in json.loads(cached)
            ])

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{TMDB_BASE_URL}/search/movie", params={
                "api_key":  TMDB_API_KEY,
                "query":    request.query,
                "language": "fr-FR",
            })

        if resp.status_code != 200:
            await context.abort(grpc.StatusCode.INTERNAL, "Erreur lors de la recherche")

        movies = [
            {
                "id": item["id"],
                "title": item["title"],
                "poster_path": item.get("poster_path") or "",
                "release_date": item.get("release_date") or "",
            }
            for item in resp.json().get("results", [])
        ]
        await redis_client.setex(cache_key, 300, json.dumps(movies))  # 5 min

        return api_consumer_pb2.MovieList(movies=[
            api_consumer_pb2.Movie(**m) for m in movies
        ])


async def serve():
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    server = aio.server()
    api_consumer_pb2_grpc.add_ApiConsumerServiceServicer_to_server(ApiConsumerServicer(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("API Consumer gRPC server listening on :50051")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
