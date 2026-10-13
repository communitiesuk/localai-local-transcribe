from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile

from common.audio.ffmpeg import convert_to_mp3
from evals.transcription.src.core.ami.cache import AMICacheEntry, AMISampleCache, CorruptCacheEntryError
from evals.transcription.src.models import MeetingSegment

SEGMENT = MeetingSegment(meeting_id="ES2008a", utterance_cutoff_time=None)
DIARIZATION = [{"speaker": "A", "start_time": 0.0, "end_time": 1.0, "text": "hello world"}]


def _entry(tmp_path, index: int = 5) -> AMISampleCache:
    return AMISampleCache(tmp_path, SEGMENT, index)


def test_sample_cache_derives_all_three_paths(tmp_path):
    entry = _entry(tmp_path)

    assert entry.audio == tmp_path / "ES2008a_000005_full.mp3"
    assert entry.transcript == tmp_path / "ES2008a_000005_full.txt"
    assert entry.diarization == tmp_path / "ES2008a_000005_full_ref_diarization.json"


def test_sample_cache_key_separates_truncated_from_full_meetings(tmp_path):
    full = AMISampleCache(tmp_path, MeetingSegment(meeting_id="ES2008a"), 0)
    truncated = AMISampleCache(tmp_path, MeetingSegment(meeting_id="ES2008a", utterance_cutoff_time=172.4), 0)

    assert full.audio != truncated.audio
    assert full.transcript != truncated.transcript
    assert full.diarization != truncated.diarization
    assert truncated.audio == tmp_path / "ES2008a_000000_c172.4.mp3"


def test_sample_cache_key_separates_different_cutoffs(tmp_path):
    """Two different fractions of the same meeting are different artefacts."""
    ten_percent = AMISampleCache(tmp_path, MeetingSegment(meeting_id="ES2008a", utterance_cutoff_time=214.0), 0)
    half = AMISampleCache(tmp_path, MeetingSegment(meeting_id="ES2008a", utterance_cutoff_time=1071.0), 0)

    assert ten_percent.audio != half.audio


def test_a_truncated_entry_is_not_a_cache_hit_for_a_full_run(tmp_path, monkeypatch):
    """The regression this key guards: a complete 10% entry must not satisfy a full run."""

    def fake_convert(input_path, output_path):
        output_path.write_bytes(input_path.read_bytes())

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", fake_convert)

    truncated = AMISampleCache(tmp_path, MeetingSegment(meeting_id="ES2008a", utterance_cutoff_time=172.4), 0)
    truncated.write(np.array([0.1, 0.2], dtype=np.float32), 16000, "partial", DIARIZATION)
    assert truncated.is_complete() is True

    full = AMISampleCache(tmp_path, MeetingSegment(meeting_id="ES2008a"), 0)
    assert full.is_complete() is False


def test_sample_cache_is_complete_when_every_artefact_exists(tmp_path):
    entry = _entry(tmp_path)
    entry.audio.write_bytes(b"audio")
    entry.transcript.write_text("hello world", encoding="utf-8")
    entry.diarization.write_text(json.dumps(DIARIZATION), encoding="utf-8")

    assert entry.is_complete() is True


@pytest.mark.parametrize("missing", ["audio", "transcript", "diarization"])
def test_sample_cache_is_incomplete_when_any_artefact_missing(tmp_path, missing):
    """A half-written entry must report itself incomplete so the loader rebuilds it."""
    entry = _entry(tmp_path)
    written = {
        "audio": lambda: entry.audio.write_bytes(b"audio"),
        "transcript": lambda: entry.transcript.write_text("hello world", encoding="utf-8"),
        "diarization": lambda: entry.diarization.write_text(json.dumps(DIARIZATION), encoding="utf-8"),
    }
    for name, write in written.items():
        if name != missing:
            write()

    assert entry.is_complete() is False


def test_sample_cache_round_trips_all_three_artefacts(tmp_path, monkeypatch):
    audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    def fake_convert(input_path, output_path):
        output_path.write_bytes(input_path.read_bytes())

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", fake_convert)

    entry = _entry(tmp_path)
    entry.write(audio_data, 16000, "hello world", DIARIZATION)

    assert entry.is_complete() is True

    loaded = entry.read()
    assert loaded.sample_rate == 16000
    assert loaded.text == "hello world"
    assert loaded.reference_diarization == DIARIZATION
    np.testing.assert_allclose(loaded.audio, audio_data, rtol=1e-3, atol=1e-4)


def test_read_raises_a_named_error_for_a_corrupt_entry(tmp_path):
    """Corruption from outside this class surfaces as an actionable error, not a decode error."""
    entry = _entry(tmp_path)
    entry.audio.parent.mkdir(parents=True, exist_ok=True)
    entry.transcript.write_text("text", encoding="utf-8")
    entry.diarization.write_text("{not json", encoding="utf-8")
    entry.audio.write_bytes(b"not audio")

    assert entry.is_complete() is True
    with pytest.raises(CorruptCacheEntryError, match="present but unreadable"):
        entry.read()


@pytest.mark.parametrize("cutoff", [1.1, 1.4])
def test_cache_key_retains_fractional_cutoff(tmp_path, cutoff):
    entry = AMISampleCache(tmp_path, MeetingSegment(meeting_id="meeting", utterance_cutoff_time=cutoff), 0)
    assert entry.audio.name == f"meeting_000000_c{cutoff!r}.mp3"


@pytest.mark.parametrize("corrupt_file", ["diarization", "transcript"])
def test_corrupt_text_artefact_with_valid_audio_names_only_affected_entry(tmp_path, corrupt_file):
    entry = _entry(tmp_path)
    soundfile.write(entry.audio, np.zeros(160), 16000, format="WAV")
    entry.transcript.write_text("hello", encoding="utf-8")
    entry.diarization.write_text("[]", encoding="utf-8")
    getattr(entry, corrupt_file).write_bytes(b"{invalid" if corrupt_file == "diarization" else b"\xff")
    with pytest.raises(CorruptCacheEntryError) as error:
        entry.read()
    for path in (entry.audio, entry.transcript, entry.diarization):
        assert str(path) in str(error.value)


def test_cache_entry_equality_does_not_compare_numpy_arrays():
    first = AMICacheEntry(np.array([0.1, 0.2]), "hello", [], sample_rate=16000)
    second = AMICacheEntry(np.array([0.1, 0.2]), "hello", [], sample_rate=16000)
    comparison = first == second
    assert isinstance(comparison, bool)


@pytest.mark.parametrize("stage", ["audio", "transcript", "diarization"])
def test_interrupted_rebuild_does_not_accept_truncated_audio_or_text(tmp_path, monkeypatch, stage):
    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", shutil.copyfile)
    entry = _entry(tmp_path)
    samples = np.zeros(16000, dtype=np.float32)
    entry.write(samples, 16000, "old text", DIARIZATION)
    entry.audio.unlink()  # Good siblings remain from an earlier build.
    original_write = Path.write_text

    def interrupted_convert(source, target):
        target.write_bytes(source.read_bytes()[:100])
        message = "encode interrupted"
        raise RuntimeError(message)

    def interrupted_text(path, text, **kwargs):
        if path == getattr(entry, stage):
            original_write(path, text[:1], **kwargs)
            message = "text write interrupted"
            raise RuntimeError(message)
        return original_write(path, text, **kwargs)

    if stage == "audio":
        monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", interrupted_convert)
    else:
        monkeypatch.setattr(Path, "write_text", interrupted_text)
    with pytest.raises(RuntimeError, match="interrupted"):
        entry.write(samples, 16000, "new text", DIARIZATION)
    if stage == "diarization":
        assert entry.is_complete()
        with pytest.raises(CorruptCacheEntryError):
            entry.read()
    else:
        assert not entry.is_complete()
        assert not entry.diarization.exists()


def _seeded_entry(tmp_path) -> AMISampleCache:
    entry = _entry(tmp_path)
    soundfile.write(entry.audio, np.zeros(160), 16000, format="WAV")
    entry.transcript.write_text("hello", encoding="utf-8")
    entry.diarization.write_text("[]", encoding="utf-8")
    return entry


@pytest.mark.skipif(os.geteuid() == 0, reason="root bypasses file permissions")
def test_unreadable_audio_does_not_advise_deleting_valid_cache(tmp_path):
    entry = _seeded_entry(tmp_path)
    entry.audio.chmod(0o000)
    try:
        with pytest.raises(PermissionError) as raised:
            entry.read()
    finally:
        entry.audio.chmod(0o644)

    assert "Delete these files" not in str(raised.value)
    assert entry.is_complete()


@pytest.mark.skipif(os.geteuid() == 0, reason="root bypasses file permissions")
def test_unreadable_transcript_does_not_advise_deleting_valid_cache(tmp_path):
    entry = _seeded_entry(tmp_path)
    entry.transcript.chmod(0o000)
    try:
        with pytest.raises(PermissionError) as raised:
            entry.read()
    finally:
        entry.transcript.chmod(0o644)

    assert "Delete these files" not in str(raised.value)
    assert entry.is_complete()


def test_real_ffmpeg_sample_cache_round_trip(tmp_path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg and ffprobe are required")
    sample_rate = 16000
    waveform = 0.2 * np.sin(2 * np.pi * 440 * np.arange(48000) / sample_rate)
    entry = _entry(tmp_path)
    entry.write(np.column_stack((waveform, waveform)), sample_rate, "hello world", DIARIZATION)
    loaded = entry.read()
    assert entry.is_complete()
    assert loaded.audio.ndim == 1
    assert len(loaded.audio) == len(waveform)
    assert soundfile.info(entry.audio).samplerate == sample_rate
    assert np.corrcoef(loaded.audio, waveform)[0, 1] > 0.99
    assert loaded.sample_rate == 16000
    assert loaded.text == "hello world"
    assert loaded.reference_diarization == DIARIZATION


def test_readable_truncated_mp3_cannot_complete_an_interrupted_rebuild(tmp_path, monkeypatch):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg and ffprobe are required")
    entry = _entry(tmp_path)
    waveform = 0.2 * np.sin(2 * np.pi * 440 * np.arange(48000) / 16000)
    entry.write(waveform, 16000, "hello world", DIARIZATION)
    entry.audio.unlink()

    def interrupted_encode(source, target):
        convert_to_mp3(source, target)
        data = target.read_bytes()
        target.write_bytes(data[: len(data) // 2])
        message = "encode interrupted"
        raise RuntimeError(message)

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", interrupted_encode)
    with pytest.raises(RuntimeError, match="encode interrupted"):
        entry.write(waveform, 16000, "hello world", DIARIZATION)
    assert not entry.audio.exists()
    assert not entry.is_complete()
    assert not entry.transcript.exists()
    assert not entry.diarization.exists()
