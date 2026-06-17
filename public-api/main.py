import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

import grpc
from grpc import aio
from fastapi import FastAPI, HTTPException, Path, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, Field

import business_logic_pb2
import business_logic_pb2_grpc

BUSINESS_LOGIC_HOST = os.getenv("BUSINESS_LOGIC_HOST", "business-logic:50051")
JWT_SECRET          = os.getenv("JWT_SECRET", "movienight-dev-secret-change-in-prod")
JWT_ALGORITHM       = "HS256"
JWT_EXPIRY_HOURS    = 72

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

_bearer = HTTPBearer()


def _create_token(user_id: int, username: str) -> str:
    payload = {
        "sub":      str(user_id),
        "username": username,
        "exp":      datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"id": int(payload["sub"]), "username": payload["username"]}
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")


def _grpc_error_to_http(e: grpc.RpcError) -> HTTPException:
    mapping = {
        grpc.StatusCode.NOT_FOUND:         404,
        grpc.StatusCode.INVALID_ARGUMENT:  400,
        grpc.StatusCode.ALREADY_EXISTS:    409,
        grpc.StatusCode.UNAVAILABLE:       503,
        grpc.StatusCode.INTERNAL:          500,
        grpc.StatusCode.UNAUTHENTICATED:   401,
        grpc.StatusCode.PERMISSION_DENIED: 403,
    }
    return HTTPException(status_code=mapping.get(e.code(), 500), detail=e.details())


def _movie(m) -> dict:
    return {"id": m.id, "title": m.title, "poster_path": m.poster_path, "release_date": m.release_date}


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class RegisterBody(BaseModel):
    username: str
    password: str

class LoginBody(BaseModel):
    username: str
    password: str

class RatingBody(BaseModel):
    rating: float = Field(ge=0.0, le=5.0)

class WatchlistBody(BaseModel):
    movie_id: int


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/auth/register", status_code=201)
async def register(body: RegisterBody):
    try:
        resp = await _bl_stub.Register(
            business_logic_pb2.RegisterRequest(username=body.username, password=body.password)
        )
        token = _create_token(resp.id, resp.username)
        return {"token": token, "user": {"id": resp.id, "username": resp.username}}
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.post("/api/v1/auth/login")
async def login(body: LoginBody):
    try:
        resp = await _bl_stub.Login(
            business_logic_pb2.LoginRequest(username=body.username, password=body.password)
        )
        token = _create_token(resp.id, resp.username)
        return {"token": token, "user": {"id": resp.id, "username": resp.username}}
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@app.get("/api/v1/recommendation")
async def recommendation(mood: str = Query(...), group: str = Query(...)):
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


# ---------------------------------------------------------------------------
# Protected endpoints (JWT required — user_id taken from token)
# ---------------------------------------------------------------------------

@app.post("/api/v1/movies/{id}/rate", status_code=201)
async def rate_movie(
    id:   int        = Path(...),
    body: RatingBody = ...,
    user: dict       = Depends(get_current_user),
):
    try:
        resp = await _bl_stub.RateMovie(business_logic_pb2.RatingRequest(
            movie_id=id, user_id=user["id"], rating=body.rating,
        ))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.get("/api/v1/watchlist")
async def get_watchlist(user: dict = Depends(get_current_user)):
    try:
        resp = await _bl_stub.GetWatchlist(
            business_logic_pb2.UserRequest(user_id=user["id"])
        )
        return [_movie(m) for m in resp.movies]
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)


@app.post("/api/v1/watchlist", status_code=201)
async def add_to_watchlist(
    body: WatchlistBody = ...,
    user: dict          = Depends(get_current_user),
):
    try:
        resp = await _bl_stub.AddToWatchlist(business_logic_pb2.WatchlistAddRequest(
            user_id=user["id"], movie_id=body.movie_id,
        ))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise _grpc_error_to_http(e)
