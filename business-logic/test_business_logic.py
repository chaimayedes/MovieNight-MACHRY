"""
Tests unitaires – Business Logic (MovieNight)
Utilise les vrais modules pb2 générés + mocks pour les stubs gRPC.
"""

import asyncio, sys, os, pytest
from unittest.mock import AsyncMock, MagicMock, patch
import grpc

# ---------------------------------------------------------------------------
# Setup : les vrais pb2 sont dans le même dossier
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from main import _pick_top3, BusinessLogicServicer  # noqa: E402
import business_logic_pb2 as bl_pb2

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Movie:
    def __init__(self, id, title="", poster_path="", release_date=""):
        self.id, self.title, self.poster_path, self.release_date = id, title, poster_path, release_date

def _make_movies(n):
    return [_Movie(id=i, title=f"Film {i}") for i in range(n)]

def _svc(ac=None, ds=None):
    return BusinessLogicServicer(ac_stub=ac or MagicMock(), ds_stub=ds or MagicMock())

def _ctx():
    ctx = MagicMock()
    ctx.abort = AsyncMock(side_effect=Exception("aborted"))
    return ctx

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ===========================================================================
# 1. _pick_top3
# ===========================================================================

class TestPickTop3:
    def test_couple(self):
        assert [m.id for m in _pick_top3(_make_movies(10), "couple")] == [0,1,2]

    def test_solo(self):
        assert [m.id for m in _pick_top3(_make_movies(10), "solo")] == [0,2,4]

    def test_friends(self):
        assert [m.id for m in _pick_top3(_make_movies(10), "friends")] == [0,3,6]

    def test_family(self):
        assert [m.id for m in _pick_top3(_make_movies(10), "family")] == [2,5,8]

    def test_fallback_when_sparse(self):
        result = _pick_top3(_make_movies(4), "friends")  # voudrait 0,3,6 → 6 absent
        assert len(result) == 3
        assert len({m.id for m in result}) == 3          # pas de doublons

    def test_always_3_picks(self):
        for g in ("couple","solo","friends","family"):
            assert len(_pick_top3(_make_movies(20), g)) == 3

    def test_no_duplicates(self):
        result = _pick_top3(_make_movies(5), "friends")
        ids = [m.id for m in result]
        assert len(ids) == len(set(ids))




# ===========================================================================
# 4. Recommend
# ===========================================================================

class TestRecommend:
    def _ac(self, n):
        ac = MagicMock()
        ac.FetchMoviesByGenre = AsyncMock(return_value=MagicMock(movies=_make_movies(n)))
        return ac

    def test_ok(self):
        assert run(_svc(ac=self._ac(10)).Recommend(MagicMock(mood="chill", group="couple"), _ctx())) is not None

    def test_invalid_mood_aborts(self):
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=self._ac(10)).Recommend(MagicMock(mood="YOLO", group="solo"), _ctx()))

    def test_invalid_group_aborts(self):
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=self._ac(10)).Recommend(MagicMock(mood="action", group="YOLO"), _ctx()))

    def test_no_movies_aborts(self):
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=self._ac(0)).Recommend(MagicMock(mood="scary", group="friends"), _ctx()))

    def test_ac_unavailable_aborts(self):
        ac = MagicMock(); ac.FetchMoviesByGenre = AsyncMock(side_effect=grpc.RpcError())
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=ac).Recommend(MagicMock(mood="cry", group="family"), _ctx()))

    @pytest.mark.parametrize("mood", ["chill","scary","laugh","cry","action"])
    def test_all_moods_accepted(self, mood):
        assert run(_svc(ac=self._ac(10)).Recommend(MagicMock(mood=mood, group="solo"), _ctx())) is not None


# ===========================================================================
# 5. Search
# ===========================================================================

class TestSearch:
    def test_ok(self):
        ac = MagicMock(); ac.SearchMovies = AsyncMock(return_value=MagicMock(movies=_make_movies(3)))
        assert run(_svc(ac=ac).Search(MagicMock(query="Matrix"), _ctx())) is not None

    def test_empty_query_aborts(self):
        with pytest.raises(Exception, match="aborted"):
            run(_svc().Search(MagicMock(query="   "), _ctx()))

    def test_ac_unavailable_aborts(self):
        ac = MagicMock(); ac.SearchMovies = AsyncMock(side_effect=grpc.RpcError())
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=ac).Search(MagicMock(query="Inception"), _ctx()))


# ===========================================================================
# 6. RateMovie
# ===========================================================================

class TestRateMovie:
    def _ds_ok(self):
        ds = MagicMock(); ds.SaveRating = AsyncMock(return_value=MagicMock()); return ds

    def test_ok(self):
        assert run(_svc(ds=self._ds_ok()).RateMovie(MagicMock(movie_id=1, user_id=1, rating=4.5), _ctx())) is not None

    def test_negative_aborts(self):
        with pytest.raises(Exception, match="aborted"):
            run(_svc().RateMovie(MagicMock(movie_id=1, user_id=1, rating=-0.1), _ctx()))

    def test_above_five_aborts(self):
        with pytest.raises(Exception, match="aborted"):
            run(_svc().RateMovie(MagicMock(movie_id=1, user_id=1, rating=5.1), _ctx()))

    @pytest.mark.parametrize("r", [0.0, 2.5, 5.0])
    def test_boundaries_ok(self, r):
        assert run(_svc(ds=self._ds_ok()).RateMovie(MagicMock(movie_id=1, user_id=1, rating=r), _ctx())) is not None

    def test_ds_unavailable_aborts(self):
        ds = MagicMock(); ds.SaveRating = AsyncMock(side_effect=grpc.RpcError())
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ds=ds).RateMovie(MagicMock(movie_id=1, user_id=1, rating=3.0), _ctx()))


# ===========================================================================
# 7. GetCatalog
# ===========================================================================

class TestGetCatalog:
    def test_ok(self):
        ac = MagicMock()
        ac.FetchCatalog = AsyncMock(return_value=MagicMock(total_results=100, movies=_make_movies(20)))
        assert run(_svc(ac=ac).GetCatalog(MagicMock(page=1, limit=20), _ctx())) is not None

    def test_unavailable_aborts(self):
        ac = MagicMock(); ac.FetchCatalog = AsyncMock(side_effect=grpc.RpcError())
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=ac).GetCatalog(MagicMock(page=1, limit=20), _ctx()))


# ===========================================================================
# 8. GetMovie
# ===========================================================================

class TestGetMovie:
    def test_ok(self):
        ac = MagicMock()
        ac.FetchMovie = AsyncMock(return_value=MagicMock(
            id=1, title="Matrix", overview="Neo", duration=136,
            poster_path="/x.jpg", release_date="1999-03-31",
            genres=["Action"], casting=["Keanu"],
        ))
        assert run(_svc(ac=ac).GetMovie(MagicMock(movie_id=1), _ctx())) is not None

    def test_not_found_aborts(self):
        ac = MagicMock()
        e = grpc.RpcError(); e.code = lambda: grpc.StatusCode.NOT_FOUND; e.details = lambda: "Film introuvable"
        ac.FetchMovie = AsyncMock(side_effect=e)
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=ac).GetMovie(MagicMock(movie_id=999), _ctx()))

    def test_unavailable_aborts(self):
        ac = MagicMock()
        e = grpc.RpcError(); e.code = lambda: grpc.StatusCode.INTERNAL; e.details = lambda: ""
        ac.FetchMovie = AsyncMock(side_effect=e)
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=ac).GetMovie(MagicMock(movie_id=1), _ctx()))


# ===========================================================================
# 9. GetWatchlist
# ===========================================================================

class TestGetWatchlist:
    def test_ok(self):
        ds = MagicMock(); ds.GetWatchlist = AsyncMock(return_value=MagicMock(movies=_make_movies(3)))
        assert run(_svc(ds=ds).GetWatchlist(MagicMock(user_id=1), _ctx())) is not None

    def test_empty(self):
        ds = MagicMock(); ds.GetWatchlist = AsyncMock(return_value=MagicMock(movies=[]))
        assert run(_svc(ds=ds).GetWatchlist(MagicMock(user_id=1), _ctx())) is not None

    def test_unavailable_aborts(self):
        ds = MagicMock(); ds.GetWatchlist = AsyncMock(side_effect=grpc.RpcError())
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ds=ds).GetWatchlist(MagicMock(user_id=1), _ctx()))


# ===========================================================================
# 10. AddToWatchlist
# ===========================================================================

class TestAddToWatchlist:
    def _ac_ok(self):
        ac = MagicMock()
        ac.FetchMovie = AsyncMock(return_value=MagicMock(
            title="Inception", poster_path="/y.jpg", release_date="2010-07-16"
        ))
        return ac

    def test_ok(self):
        ds = MagicMock(); ds.AddToWatchlist = AsyncMock(return_value=MagicMock())
        assert run(_svc(ac=self._ac_ok(), ds=ds).AddToWatchlist(MagicMock(user_id=1, movie_id=42), _ctx())) is not None

    def test_movie_not_found_aborts(self):
        ac = MagicMock()
        e = grpc.RpcError(); e.code = lambda: grpc.StatusCode.NOT_FOUND; e.details = lambda: "introuvable"
        ac.FetchMovie = AsyncMock(side_effect=e)
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=ac).AddToWatchlist(MagicMock(user_id=1, movie_id=99), _ctx()))

    def test_already_exists_aborts(self):
        ds = MagicMock()
        e = grpc.RpcError(); e.code = lambda: grpc.StatusCode.ALREADY_EXISTS; e.details = lambda: "déjà là"
        ds.AddToWatchlist = AsyncMock(side_effect=e)
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=self._ac_ok(), ds=ds).AddToWatchlist(MagicMock(user_id=1, movie_id=42), _ctx()))

    def test_ds_unavailable_aborts(self):
        ds = MagicMock()
        e = grpc.RpcError(); e.code = lambda: grpc.StatusCode.INTERNAL; e.details = lambda: ""
        ds.AddToWatchlist = AsyncMock(side_effect=e)
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ac=self._ac_ok(), ds=ds).AddToWatchlist(MagicMock(user_id=1, movie_id=42), _ctx()))


# ===========================================================================
# Register/Login — variantes patchant bcrypt (env sans bcrypt compatible)
# ===========================================================================

class TestRegisterBcryptPatched:
    """Même logique que TestRegister mais with bcrypt mocké pour les envs sans bcrypt natif."""

    def _ds_ok(self):
        ds = MagicMock()
        ds.RegisterUser = AsyncMock(return_value=MagicMock(id=1, username="alice"))
        return ds

    @patch("main.asyncio.to_thread", new_callable=AsyncMock, return_value="hashed_pw")
    def test_ok(self, _mock_thread):
        resp = run(_svc(ds=self._ds_ok()).Register(MagicMock(username="alice", password="secret"), _ctx()))
        assert resp.username == "alice"

    @patch("main.asyncio.to_thread", new_callable=AsyncMock, return_value="hashed_pw")
    def test_already_exists_aborts(self, _mock_thread):
        ds = MagicMock()
        e = grpc.RpcError(); e.code = lambda: grpc.StatusCode.ALREADY_EXISTS; e.details = lambda: ""
        ds.RegisterUser = AsyncMock(side_effect=e)
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ds=ds).Register(MagicMock(username="alice", password="secret"), _ctx()))

    @patch("main.asyncio.to_thread", new_callable=AsyncMock, return_value="hashed_pw")
    def test_datastore_unavailable_aborts(self, _mock_thread):
        ds = MagicMock()
        e = grpc.RpcError(); e.code = lambda: grpc.StatusCode.INTERNAL; e.details = lambda: ""
        ds.RegisterUser = AsyncMock(side_effect=e)
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ds=ds).Register(MagicMock(username="bob", password="pass"), _ctx()))


class TestLoginBcryptPatched:
    """Login tests avec pwd_context.verify mocké."""

    def _ds(self, valid=True):
        ds = MagicMock()
        ds.GetUserByUsername = AsyncMock(
            return_value=MagicMock(id=1, username="alice", hashed_password="hashed_pw")
        )
        return ds

    @patch("main.asyncio.to_thread", new_callable=AsyncMock, return_value=True)
    def test_correct_password(self, _):
        resp = run(_svc(ds=self._ds()).Login(MagicMock(username="alice", password="secret"), _ctx()))
        assert resp.username == "alice"

    @patch("main.asyncio.to_thread", new_callable=AsyncMock, return_value=False)
    def test_wrong_password_aborts(self, _):
        with pytest.raises(Exception, match="aborted"):
            run(_svc(ds=self._ds()).Login(MagicMock(username="alice", password="wrong"), _ctx()))
