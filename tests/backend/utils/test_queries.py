import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from backend.utils.queries import has_pending_minute_version_for_transcription
from common.database.postgres_models import JobStatus, MinuteVersion


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (JobStatus.AWAITING_START, True),
        (JobStatus.IN_PROGRESS, True),
        (JobStatus.COMPLETED, False),
        (JobStatus.FAILED, False),
    ],
)
async def test_has_pending_minute_version_for_transcription(status, expected):
    minute_version = MinuteVersion(
        id=uuid.uuid4(),
        minute_id=uuid.uuid4(),
        status=status,
    )
    transcription_id = uuid.uuid4()

    session = Mock()
    session.exec = AsyncMock()
    exec_result = Mock()
    exec_result.first.return_value = minute_version if expected else None
    session.exec.return_value = exec_result

    result = await has_pending_minute_version_for_transcription(session, transcription_id)
    assert result is expected