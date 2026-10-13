from __future__ import annotations

import shutil

import numpy as np

from evals.transcription.src.core.ami import AMIDatasetLoader, AMIDatasetSource
from evals.transcription.src.models import DatasetProtocol


def test_ami_source_returns_a_real_prepared_dataset(tmp_path, monkeypatch):
    rows = [
        {
            "meeting_id": "meeting",
            "audio_id": "utterance",
            "text": "hello world",
            "audio": {"array": np.zeros(16000, dtype=np.float32), "sampling_rate": 16000},
            "begin_time": 0.0,
            "end_time": 1.0,
            "microphone_id": "headset",
            "speaker_id": "speaker",
        }
    ]
    monkeypatch.setattr("evals.transcription.src.core.ami.metadata.load_dataset", lambda *_args, **_kwargs: rows)
    monkeypatch.setattr("evals.transcription.src.core.ami.loader.load_dataset", lambda *_args, **_kwargs: rows)
    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", shutil.copyfile)

    dataset: DatasetProtocol = AMIDatasetSource(tmp_path).load(num_samples=1)

    assert isinstance(dataset, AMIDatasetLoader)
    assert len(dataset) == 1
    assert dataset.dataset_version == "AMI_v0"
    assert dataset.dataset_split == "n1"
    assert dataset[0].text == "hello world"
    assert dataset[0].audio.array.size > 0
    assert dataset[0].reference_diarization[0]["speaker"] == "speaker"

    cached = AMIDatasetSource(tmp_path).load(num_samples=1)
    assert cached[0].text == dataset[0].text
    np.testing.assert_allclose(cached[0].audio.array, dataset[0].audio.array)
