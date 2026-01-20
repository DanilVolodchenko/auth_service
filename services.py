import uuid

import jwt
from fastapi import HTTPException
from dotenv import dotenv_values

config = dotenv_values('.env')


class AuthService:
    game_id__players: dict[uuid.UUID, list[str]] = {}

    @classmethod
    def create_game_for_players(cls, players: list[str]) -> dict[str, uuid.UUID]:
        game_id = uuid.uuid4()

        cls.game_id__players[game_id] = players

        return {'game_id': game_id}

    @classmethod
    def create_jwt_token(cls, player_id: str, game_id: uuid.UUID) -> dict[str, str]:
        try:
            if player_id not in cls.game_id__players[game_id]:
                raise HTTPException(status_code=403, detail='У игрока нет доступа до игры')
        except KeyError:
            raise HTTPException(status_code=403, detail='Такой игры не существует')

        token = jwt.encode({'game_id': str(game_id)}, config['SECRET_KEY'], algorithm='HS256')

        return {'token': token}
