from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from custom.config import CustomizationConfig
from custom.web.router import create_customization_router


@pytest.fixture
def test_app():
    app = FastAPI()
    router = create_customization_router()
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


def test_get_config(client):
    with patch('custom.services.customization_service.customization_service.get_config', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = CustomizationConfig(enabled=True)
        resp = client.get('/api/customization/config')
        assert resp.status_code == 200
        data = resp.json()
        assert data['enabled'] is True
        assert 'pages' in data


def test_update_config(client):
    with patch('custom.services.customization_service.customization_service.update_config', new_callable=AsyncMock) as mock_update:
        updated = CustomizationConfig(enabled=True)
        updated.needs_restart = True
        mock_update.return_value = updated

        resp = client.post('/api/customization/config', json={'enabled': True})
        assert resp.status_code == 200
        data = resp.json()
        assert data['enabled'] is True
        assert data['needs_restart'] is True


def test_auto_translate_endpoint(client):
    with patch('custom.web.router.language_service.auto_translate_text', new_callable=AsyncMock) as mock_tr:
        mock_tr.return_value = {'en': 'Hello', 'ua': 'Привіт'}

        resp = client.post('/api/customization/translate', json={'text': 'Привет', 'source_lang': 'ru'})
        assert resp.status_code == 200
        data = resp.json()
        assert data['translations']['en'] == 'Hello'
        assert data['translations']['ua'] == 'Привіт'


def test_emoji_pack_endpoint(client):
    with patch('custom.services.emoji_service.emoji_service.add_emoji_pack', new_callable=AsyncMock) as mock_add:
        mock_add.return_value = {
            'name': 'cool_vpn_emojis',
            'url': 'https://t.me/addemoji/cool_vpn_emojis',
            'count': 5,
        }

        resp = client.post(
            '/api/customization/emoji-pack',
            json={'url': 'https://t.me/addemoji/cool_vpn_emojis', 'name': 'cool_vpn_emojis'},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['name'] == 'cool_vpn_emojis'


def test_customization_page_html(client):
    resp = client.get('/customization')
    assert resp.status_code == 200
    assert 'text/html' in resp.headers['content-type']
    assert 'Кастомизация бота' in resp.text
