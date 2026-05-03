import pytest
from unittest.mock import AsyncMock, MagicMock
from redis.exceptions import ConnectionError, TimeoutError
from backend.database.redis import JWTDenylist


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.set = AsyncMock(return_value=True)
    r.exists = AsyncMock(return_value=0)
    return r


# --- add() ---

@pytest.mark.asyncio
async def test_add_sets_key_with_correct_ttl(mock_redis):
    denylist = JWTDenylist(mock_redis)
    result = await denylist.add("abc-123", 300)
    assert result is True
    mock_redis.set.assert_awaited_once_with("jwt:deny:abc-123", "1", ex=300)


@pytest.mark.asyncio
async def test_add_clamps_ttl_to_minimum_one(mock_redis):
    denylist = JWTDenylist(mock_redis)
    await denylist.add("abc-123", 0)
    mock_redis.set.assert_awaited_once_with("jwt:deny:abc-123", "1", ex=1)


@pytest.mark.asyncio
async def test_add_returns_false_when_redis_is_none():
    denylist = JWTDenylist(None)
    result = await denylist.add("abc-123", 300)
    assert result is False


@pytest.mark.asyncio
async def test_add_returns_false_on_connection_error(mock_redis):
    mock_redis.set = AsyncMock(side_effect=ConnectionError("down"))
    denylist = JWTDenylist(mock_redis)
    result = await denylist.add("abc-123", 300)
    assert result is False


@pytest.mark.asyncio
async def test_add_returns_false_on_timeout(mock_redis):
    mock_redis.set = AsyncMock(side_effect=TimeoutError("timeout"))
    denylist = JWTDenylist(mock_redis)
    result = await denylist.add("abc-123", 300)
    assert result is False


# --- is_denied() ---

@pytest.mark.asyncio
async def test_is_denied_returns_true_when_key_exists(mock_redis):
    mock_redis.exists = AsyncMock(return_value=1)
    denylist = JWTDenylist(mock_redis)
    assert await denylist.is_denied("abc-123") is True


@pytest.mark.asyncio
async def test_is_denied_returns_false_when_key_absent(mock_redis):
    mock_redis.exists = AsyncMock(return_value=0)
    denylist = JWTDenylist(mock_redis)
    assert await denylist.is_denied("abc-123") is False


@pytest.mark.asyncio
async def test_is_denied_fail_open_when_redis_is_none():
    denylist = JWTDenylist(None)
    assert await denylist.is_denied("abc-123") is False


@pytest.mark.asyncio
async def test_is_denied_fail_open_on_connection_error(mock_redis):
    mock_redis.exists = AsyncMock(side_effect=ConnectionError("down"))
    denylist = JWTDenylist(mock_redis)
    assert await denylist.is_denied("abc-123") is False


@pytest.mark.asyncio
async def test_is_denied_fail_open_on_timeout(mock_redis):
    mock_redis.exists = AsyncMock(side_effect=TimeoutError("timeout"))
    denylist = JWTDenylist(mock_redis)
    assert await denylist.is_denied("abc-123") is False


@pytest.mark.asyncio
async def test_key_format(mock_redis):
    """Key must be jwt:deny:{jti} — never jwt:deny: or a different prefix."""
    denylist = JWTDenylist(mock_redis)
    await denylist.add("my-jti-value", 60)
    call_args = mock_redis.set.call_args[0]
    assert call_args[0] == "jwt:deny:my-jti-value"
