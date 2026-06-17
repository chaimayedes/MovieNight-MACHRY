import asyncio
import os
from typing import Optional
import grpc
from grpc import aio
from sqlmodel import SQLModel, Field, Session, create_engine, select
import datastore_pb2
import datastore_pb2_grpc

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/movie_night.db")
engine = create_engine(DATABASE_URL, echo=False)


class Rating(SQLModel, table=True):
    id:       Optional[int] = Field(default=None, primary_key=True)
    movie_id: int
    user_id:  int
    rating:   float


class WatchlistEntry(SQLModel, table=True):
    id:           Optional[int] = Field(default=None, primary_key=True)
    user_id:      int
    movie_id:     int
    title:        str
    poster_path:  str = ""
    release_date: str = ""


def _create_tables():
    SQLModel.metadata.create_all(engine)


class DatastoreServicer(datastore_pb2_grpc.DatastoreServiceServicer):

    async def SaveRating(self, request, context):
        if not (0.0 <= request.rating <= 5.0):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "La note doit être entre 0 et 5")

        def _save():
            with Session(engine) as session:
                session.add(Rating(
                    movie_id=request.movie_id,
                    user_id=request.user_id,
                    rating=request.rating,
                ))
                session.commit()

        await asyncio.to_thread(_save)
        return datastore_pb2.OperationResponse(
            status="success",
            message=f"Note {request.rating} enregistrée pour le film {request.movie_id}",
        )

    async def GetWatchlist(self, request, context):
        def _fetch():
            with Session(engine) as session:
                return session.exec(
                    select(WatchlistEntry).where(WatchlistEntry.user_id == request.user_id)
                ).all()

        entries = await asyncio.to_thread(_fetch)
        return datastore_pb2.MovieList(movies=[
            datastore_pb2.Movie(
                id=e.movie_id,
                title=e.title,
                poster_path=e.poster_path,
                release_date=e.release_date,
            )
            for e in entries
        ])

    async def AddToWatchlist(self, request, context):
        def _add():
            with Session(engine) as session:
                existing = session.exec(
                    select(WatchlistEntry).where(
                        WatchlistEntry.user_id  == request.user_id,
                        WatchlistEntry.movie_id == request.movie_id,
                    )
                ).first()
                if existing:
                    return False
                session.add(WatchlistEntry(
                    user_id=request.user_id,
                    movie_id=request.movie_id,
                    title=request.title,
                    poster_path=request.poster_path,
                    release_date=request.release_date,
                ))
                session.commit()
                return True

        added = await asyncio.to_thread(_add)
        if not added:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, "Film déjà dans la watchlist")

        return datastore_pb2.OperationResponse(
            status="success",
            message=f"Film {request.movie_id} ajouté à la watchlist",
        )


async def serve():
    _create_tables()
    server = aio.server()
    datastore_pb2_grpc.add_DatastoreServiceServicer_to_server(DatastoreServicer(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("Datastore gRPC server listening on :50051")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
