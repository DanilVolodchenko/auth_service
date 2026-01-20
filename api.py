import uuid
from dataclasses import dataclass

from fastapi import APIRouter

from services import AuthService


@dataclass(slots=True, frozen=True)
class GameInfo:
    player_id: str
    game_id: uuid.UUID


router = APIRouter(tags=['Auth'], prefix='/api/v1')


@router.post('/game/create')
def create_game(players: list[str]) -> dict[str, uuid.UUID]:
    """Возвращает id созданной игры."""

    return AuthService.create_game_for_players(players)


@router.post('/auth')
def get_jwt_token(game_info: GameInfo):
    """Создает JWT токен игры."""
    return AuthService.create_jwt_token(game_info.player_id, game_info.game_id)
