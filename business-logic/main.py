import asyncio
import os
import grpc
from grpc import aio
import api_consumer_pb2
import api_consumer_pb2_grpc
import datastore_pb2
import datastore_pb2_grpc
import business_logic_pb2
import business_logic_pb2_grpc

API_CONSUMER_HOST = os.getenv("API_CONSUMER_HOST", "api-consumer:50051")
DATASTORE_HOST    = os.getenv("DATASTORE_HOST",    "datastore:50051")

VALID_MOODS  = {"chill", "scary", "laugh", "cry", "action"}
VALID_GROUPS = {"solo", "couple", "friends", "family"}

# Each group selects differently from the popularity-sorted list returned by api-consumer.
# (start_index, step) → picks movies at positions [start, start+step, start+2*step]
#   couple  → 0,1,2  (mainstream safe picks)
#   solo    → 0,2,4  (mix of popular and slightly niche)
#   friends → 0,3,6  (spread across the list for variety)
#   family  → 2,3,5  (skips the edgiest top picks)
GROUP_SELECTION = {
    "couple":  (0, 1),
    "solo":    (0, 2),
    "friends": (0, 3),
    "family":  (2, 3),
}


def _pick_top3(movies: list, group: str) -> list:
    start, step = GROUP_SELECTION[group]
    indices = [start + i * step for i in range(3)]
    picks   = [movies[i] for i in indices if i < len(movies)]

    if len(picks) < 3:
        seen = {m.id for m in picks}
        for m in movies:
            if len(picks) == 3:
                break
            if m.id not in seen:
                picks.append(m)
                seen.add(m.id)

    return picks[:3]


class BusinessLogicServicer(business_logic_pb2_grpc.BusinessLogicServiceServicer):

    def __init__(self, ac_stub, ds_stub):
        self.ac = ac_stub   # ApiConsumerServiceStub
        self.ds = ds_stub   # DatastoreServiceStub

    # ------------------------------------------------------------------
    # RECOMMENDATION
    # ------------------------------------------------------------------

    async def Recommend(self, request, context):
        if request.mood not in VALID_MOODS:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Humeur invalide : '{request.mood}'. Valeurs acceptées : {sorted(VALID_MOODS)}",
            )
        if request.group not in VALID_GROUPS:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Groupe invalide : '{request.group}'. Valeurs acceptées : {sorted(VALID_GROUPS)}",
            )

        try:
            resp = await self.ac.FetchMoviesByGenre(api_consumer_pb2.MoodRequest(mood=request.mood))
        except grpc.RpcError:
            await context.abort(grpc.StatusCode.UNAVAILABLE, "Service api-consumer indisponible")

        movies = list(resp.movies)
        if not movies:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Aucun film trouvé pour cette humeur")

        top3 = _pick_top3(movies, request.group)
        return business_logic_pb2.MovieList(movies=[
            business_logic_pb2.Movie(
                id=m.id, title=m.title,
                poster_path=m.poster_path, release_date=m.release_date,
            )
            for m in top3
        ])

    # ------------------------------------------------------------------
    # CATALOGUE
    # ------------------------------------------------------------------

    async def GetCatalog(self, request, context):
        try:
            resp = await self.ac.FetchCatalog(api_consumer_pb2.CatalogRequest(
                page=request.page or 1, limit=request.limit or 20,
            ))
        except grpc.RpcError:
            await context.abort(grpc.StatusCode.UNAVAILABLE, "Service api-consumer indisponible")

        return business_logic_pb2.CatalogResponse(
            total_results=resp.total_results,
            movies=[
                business_logic_pb2.Movie(
                    id=m.id, title=m.title,
                    poster_path=m.poster_path, release_date=m.release_date,
                )
                for m in resp.movies
            ],
        )

    # ------------------------------------------------------------------
    # DÉTAILS D'UN FILM
    # ------------------------------------------------------------------

    async def GetMovie(self, request, context):
        try:
            resp = await self.ac.FetchMovie(api_consumer_pb2.MovieIdRequest(movie_id=request.movie_id))
        except grpc.RpcError as e:
            code = grpc.StatusCode.NOT_FOUND if e.code() == grpc.StatusCode.NOT_FOUND else grpc.StatusCode.UNAVAILABLE
            await context.abort(code, e.details())

        return business_logic_pb2.MovieDetailed(
            id=resp.id, title=resp.title, overview=resp.overview,
            duration=resp.duration, poster_path=resp.poster_path,
            release_date=resp.release_date,
            genres=list(resp.genres), casting=list(resp.casting),
        )

    # ------------------------------------------------------------------
    # RECHERCHE
    # ------------------------------------------------------------------

    async def Search(self, request, context):
        if not request.query.strip():
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Le paramètre 'query' ne peut pas être vide")

        try:
            resp = await self.ac.SearchMovies(api_consumer_pb2.SearchRequest(query=request.query))
        except grpc.RpcError:
            await context.abort(grpc.StatusCode.UNAVAILABLE, "Service api-consumer indisponible")

        return business_logic_pb2.MovieList(movies=[
            business_logic_pb2.Movie(
                id=m.id, title=m.title,
                poster_path=m.poster_path, release_date=m.release_date,
            )
            for m in resp.movies
        ])

    # ------------------------------------------------------------------
    # NOTATION
    # ------------------------------------------------------------------

    async def RateMovie(self, request, context):
        if not (0.0 <= request.rating <= 5.0):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "La note doit être entre 0 et 5")

        try:
            await self.ds.SaveRating(datastore_pb2.RatingRequest(
                movie_id=request.movie_id,
                user_id=request.user_id,
                rating=request.rating,
            ))
        except grpc.RpcError:
            await context.abort(grpc.StatusCode.UNAVAILABLE, "Service datastore indisponible")

        return business_logic_pb2.OperationResponse(
            status="success",
            message=f"Rating registered for movie {request.movie_id}",
        )

    # ------------------------------------------------------------------
    # WATCHLIST
    # ------------------------------------------------------------------

    async def GetWatchlist(self, request, context):
        try:
            resp = await self.ds.GetWatchlist(datastore_pb2.UserRequest(user_id=request.user_id))
        except grpc.RpcError:
            await context.abort(grpc.StatusCode.UNAVAILABLE, "Service datastore indisponible")

        return business_logic_pb2.MovieList(movies=[
            business_logic_pb2.Movie(
                id=m.id, title=m.title,
                poster_path=m.poster_path, release_date=m.release_date,
            )
            for m in resp.movies
        ])

    async def AddToWatchlist(self, request, context):
        # Enrich with movie metadata from api-consumer before persisting in datastore
        try:
            movie = await self.ac.FetchMovie(api_consumer_pb2.MovieIdRequest(movie_id=request.movie_id))
        except grpc.RpcError as e:
            code = grpc.StatusCode.NOT_FOUND if e.code() == grpc.StatusCode.NOT_FOUND else grpc.StatusCode.UNAVAILABLE
            await context.abort(code, e.details())

        try:
            await self.ds.AddToWatchlist(datastore_pb2.WatchlistAddRequest(
                user_id=request.user_id,
                movie_id=request.movie_id,
                title=movie.title,
                poster_path=movie.poster_path,
                release_date=movie.release_date,
            ))
        except grpc.RpcError as e:
            code = grpc.StatusCode.ALREADY_EXISTS if e.code() == grpc.StatusCode.ALREADY_EXISTS else grpc.StatusCode.UNAVAILABLE
            await context.abort(code, e.details())

        return business_logic_pb2.OperationResponse(
            status="success",
            message=f"Film {request.movie_id} ajouté à la watchlist",
        )


async def serve():
    ac_channel = aio.insecure_channel(API_CONSUMER_HOST)
    ds_channel = aio.insecure_channel(DATASTORE_HOST)

    servicer = BusinessLogicServicer(
        ac_stub=api_consumer_pb2_grpc.ApiConsumerServiceStub(ac_channel),
        ds_stub=datastore_pb2_grpc.DatastoreServiceStub(ds_channel),
    )

    server = aio.server()
    business_logic_pb2_grpc.add_BusinessLogicServiceServicer_to_server(servicer, server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("Business Logic gRPC server listening on :50051")

    try:
        await server.wait_for_termination()
    finally:
        await ac_channel.close()
        await ds_channel.close()


if __name__ == "__main__":
    asyncio.run(serve())
