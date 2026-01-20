import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_auth_service_state():
    from services import AuthService
    old_state = AuthService.game_id__players.copy()

    AuthService.game_id__players.clear()

    yield

    AuthService.game_id__players = old_state


class TestCreateGame:
    """Тесты для endpoint создания игры"""

    def test_create_game_success(self):
        """Успешное создание игры"""
        players = ['player1', 'player2', 'player3']

        response = client.post('/api/v1/game/create', json=players)

        assert response.status_code == 200
        data = response.json()
        assert 'game_id' in data
        try:
            uuid.UUID(data['game_id'])
        except ValueError:
            pytest.fail('game_id is not a valid UUID')

    def test_create_game_empty_players(self):
        """Создание игры с пустым списком игроков"""
        players = []

        response = client.post('/api/v1/game/create', json=players)

        assert response.status_code == 200
        data = response.json()
        assert 'game_id' in data


class TestAuthEndpoint:
    """Тесты для endpoint аутентификации"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        players = ['player1', 'player2']
        response = client.post('/api/v1/game/create', json=players)
        self.game_id = response.json()['game_id']

    def test_auth_success(self):
        """Успешное получение токена"""
        game_info = {
            'player_id': 'player1',
            'game_id': self.game_id
        }

        response = client.post('/api/v1/auth', json=game_info)

        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert isinstance(data['token'], str)

    def test_auth_player_not_in_game(self):
        """Попытка получения токена для игрока не из этой игры"""
        game_info = {
            'player_id': 'player3',
            'game_id': self.game_id
        }

        response = client.post('/api/v1/auth', json=game_info)

        assert response.status_code == 403
        assert response.json()['detail'] == 'У игрока нет доступа до игры'

    def test_auth_invalid_game_id(self):
        """Попытка получения токена с несуществующим game_id"""
        invalid_game_id = str(uuid.uuid4())
        game_info = {
            'player_id': 'player1',
            'game_id': invalid_game_id
        }

        response = client.post('/api/v1/auth', json=game_info)

        assert response.status_code == 403

    def test_auth_invalid_uuid_format(self):
        """Тест с невалидным форматом UUID"""
        game_info = {
            'player_id': 'player1',
            'game_id': 'not-a-uuid'
        }

        response = client.post('/api/v1/auth', json=game_info)

        assert response.status_code == 422


class TestAuthService:
    """Тесты для AuthService"""

    def test_create_game_for_players(self):
        """Тест создания игры в сервисе"""
        from services import AuthService

        players = ['player1', 'player2']
        result = AuthService.create_game_for_players(players)

        assert 'game_id' in result
        game_id = result['game_id']

        assert game_id in AuthService.game_id__players
        assert AuthService.game_id__players[game_id] == players

    def test_create_jwt_token_success(self):
        """Тест успешного создания JWT токена"""
        from services import AuthService

        players = ['player1', 'player2']
        game_result = AuthService.create_game_for_players(players)
        game_id = game_result['game_id']

        with patch('services.config', {'SECRET_KEY': 'test_secret'}):
            with patch('services.jwt.encode') as mock_encode:
                mock_encode.return_value = 'mocked_token'

                result = AuthService.create_jwt_token('player1', game_id)

                assert result['token'] == 'mocked_token'
                mock_encode.assert_called_once_with(
                    {'game_id': str(game_id)},
                    'test_secret',
                    algorithm='HS256'
                )

    def test_create_jwt_token_player_not_found(self):
        """Тест создания токена для игрока не из игры"""
        from services import AuthService
        from fastapi import HTTPException

        players = ['player1', 'player2']
        game_result = AuthService.create_game_for_players(players)
        game_id = game_result['game_id']

        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_jwt_token('player3', game_id)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == 'У игрока нет доступа до игры'
