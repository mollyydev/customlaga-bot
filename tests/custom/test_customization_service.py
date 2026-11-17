import json
from unittest.mock import AsyncMock, patch

import pytest

from custom.config import CustomizationConfig
from custom.services.customization_service import CustomizationService


@pytest.fixture
def temp_customization_file(tmp_path):
    json_path = tmp_path / 'customization.json'
    with patch('custom.services.customization_service.CUSTOMIZATION_FILE_PATH', json_path):
        yield json_path


@pytest.mark.asyncio
async def test_service_initialization_with_missing_json(temp_customization_file):
    service = CustomizationService()
    service._cache = None
    service._db_synced = False

    mock_db = AsyncMock()
    # Mock SystemSetting lookup in DB -> None
    mock_execute = AsyncMock()
    mock_execute.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_execute

    config = await service.get_config(mock_db)
    assert config is not None
    assert config.enabled is False
    assert temp_customization_file.exists(), 'JSON file should be written if missing'


@pytest.mark.asyncio
async def test_service_realtime_update(temp_customization_file):
    service = CustomizationService()
    mock_db = AsyncMock()

    # Initial state
    config = CustomizationConfig(enabled=False)
    service._cache = config

    # Update config in realtime
    updated_data = config.to_dict()
    updated_data['enabled'] = True
    updated_data['default_language'] = 'en'

    result = await service.update_config(mock_db, updated_data)
    assert result.enabled is True
    assert result.default_language == 'en'
    assert result.needs_restart is True, 'Warning flag about restart should be set on modification'
    assert service.is_enabled() is True


@pytest.mark.asyncio
async def test_service_sync_to_file(temp_customization_file):
    service = CustomizationService()

    config = CustomizationConfig(enabled=True)
    config.needs_restart = True
    service._cache = config

    await service.sync_to_disk()
    assert temp_customization_file.exists()
    content = json.loads(temp_customization_file.read_text(encoding='utf-8'))
    assert content['enabled'] is True
    assert content['needs_restart'] is False, 'After syncing to disk, needs_restart should reset'
