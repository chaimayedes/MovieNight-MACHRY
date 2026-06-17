import os
from contextlib import asynccontextmanager
from typing import Optional

import grpc
from grpc import aio
from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

import business_logic_pb2
import business_logic_pb2_grpc

BUSINESS_LOGIC_HOST = os.getenv("BUSINESS_LOGIC_HOST", "business-logic:50051")

_bl_channel: aio.Channel = None
_bl_stub:    business_logic_pb2_grpc.BusinessLogicServiceStub = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bl_channel, _bl_stub
    _bl_channel = aio.insecure_channel(BUSINESS_LOGIC_HOST)
    _bl_stub    = business_logic_pb2_grpc.BusinessLogicServiceStub(_bl_channel)
    yield
    await _bl_channel.close()


app = FastAPI(title="Movie Night — Public API Gateway", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _grpc_error_to_http(e: grpc.RpcError) -> HTTPException:
    mapping = {
        grpc.StatusCode.NOT_FOUND:        404,
        grpc.StatusCode.INVALID_ARGUMENT: 400,
        grpc.StatusCode.ALREADY_EXISTS:   409,
        grpc.StatusCode.UNAVAILABLE:      503,
        grpc.StatusCode.INTERNAL:         500,
    }
    return HTTPException(status_code=mapping.get(e.code(), 500), detail=e.details())


def _movie(m) -> dict:
    return {"id": m.id, "title": m.title, "poster_path": m.poster_path, "release_date": m.release_date}


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class RatingBody(BaseModel):
    user_id: int
    rating:  float = Field(ge=0.0, le=5.0)


class WatchlistBody(BaseModel):
    movie_id: int


# ---------------------------------------------------------------------------
# Endpoints — miroir exact du swagger.yml
# ---------------------------------------------------------------------------

@app.get("/api/v1/recommendation")
async def recommendation(
    mood:  str = Query(...),
    group: str = Query(...),
):
    try:
        resp = await _bl_stub.Recommend(
            business_logic_pb2.RecommendRequest(mood=mood, group=group)
        )
        return [_movie(m) for m in resp.movies]
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.get("/api/v1/movies")
async def get_catalog(page: int = 1, limit: int = 20):
    try:
        resp = await _bl_stub.GetCatalog(
            business_logic_pb2.CatalogRequest(page=page, limit=limit)
        )
        return {"total_results": resp.total_results, "data": [_movie(m) for m in resp.movies]}
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.get("/api/v1/movies/{id}")
async def get_movie(id: int = Path(...)):
    try:
        resp = await _bl_stub.GetMovie(business_logic_pb2.MovieIdRequest(movie_id=id))
        return {
            "id": resp.id, "title": resp.title, "overview": resp.overview,
            "duration": resp.duration, "poster_path": resp.poster_path,
            "release_date": resp.release_date,
            "genres": list(resp.genres), "casting": list(resp.casting),
        }
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.get("/api/v1/search")
async def search(query: str = Query(...), genre: Optional[str] = None):
    try:
        resp = await _bl_stub.Search(
            business_logic_pb2.SearchRequest(query=query, genre=genre or "")
        )
        return [_movie(m) for m in resp.movies]
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.post("/api/v1/movies/{id}/rate", status_code=201)
async def rate_movie(id: int = Path(...), body: RatingBody = ...):
    try:
        resp = await _bl_stub.RateMovie(business_logic_pb2.RatingRequest(
            movie_id=id, user_id=body.user_id, rating=body.rating,
        ))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.get("/api/v1/user/{user_id}/watchlist")
async def get_watchlist(user_id: int = Path(...)):
    try:
        resp = await _bl_stub.GetWatchlist(business_logic_pb2.UserRequest(user_id=user_id))
        return [_movie(m) for m in resp.movies]
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.post("/api/v1/user/{user_id}/watchlist", status_code=201)
async def add_to_watchlist(user_id: int = Path(...), body: WatchlistBody = ...):
    try:
        resp = await _bl_stub.AddToWatchlist(business_logic_pb2.WatchlistAddRequest(
            user_id=user_id, movie_id=body.movie_id,
        ))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)
