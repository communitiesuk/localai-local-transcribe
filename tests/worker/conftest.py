from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def stopped():
    stopped = Mock()
    stopped.get = AsyncMock()
    # run once (False) then stop (True)
    stopped.get.remote = AsyncMock(side_effect=[False, True])
    return stopped


@pytest.fixture
def transcription_queue():
    return Mock()


@pytest.fixture
def llm_queue():
    return Mock()


@pytest.fixture
def actor():
    mock_actor = Mock()
    mock_actor.process = Mock()
    mock_actor.process.remote = Mock(return_value="call")
    return mock_actor
