from __future__ import annotations

import json
import shutil
from collections import Counter
from unittest.mock import Mock

import numpy as np
import pytest
import soundfile
import yaml

from common.audio.ffmpeg import convert_to_mp3
from evals.transcription.src.constants import WORKDIR
from evals.transcription.src.core.dataset import load_benchmark_dataset
from evals.transcription.src.core.english_dialects import EnglishDialectsDataset
from evals.transcription.src.core.english_dialects.english_dialects_dataset import ALL_SUBSETS, EnglishDialectsSource
from evals.transcription.src.core.results import save_results
from evals.transcription.src.core.runner import run_engines_parallel
from tests.evals.transcription.conftest import FakeAdapter


@pytest.fixture(autouse=True)
def isolated_audio_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("evals.transcription.src.core.benchmark_dataset_source.INPUT_DIR", tmp_path)
    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", shutil.copyfile)


class _FakeRows(list):
    def select_columns(self, columns):
        return _FakeRows([{key: row[key] for key in columns} for row in self])

    def __getitem__(self, key):
        if isinstance(key, str):
            return [row[key] for row in self]
        return super().__getitem__(key)


def _row(speaker_id: int, line_id: str, text: str = "hello") -> dict:
    return {
        "audio": {"array": np.array([0.0, 0.1]), "sampling_rate": 48000, "path": "sample.wav"},
        "text": text,
        "speaker_id": speaker_id,
        "line_id": line_id,
    }


def test_dataset_indexes_across_subsets_and_preserves_metadata(monkeypatch, tmp_path):
    rows = {
        "irish_male": _FakeRows([_row(1, "IR0001")]),
        "welsh_female": _FakeRows([_row(2, "WE0001"), _row(2, "WE0002")]),
    }
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, subset, **_kwargs: rows[subset],
    )

    dataset = EnglishDialectsDataset(cache_dir=tmp_path, subsets=("irish_male", "welsh_female"))

    assert len(dataset) == 3
    assert dataset.dataset_split == "published_train_all"
    assert dataset[0].dialect == "irish"
    assert dataset[0].gender == "male"
    assert dataset[1].dialect == "welsh"
    assert dataset[2].line_id == "WE0002"
    assert dataset.supports_diarization is False


def test_dataset_applies_global_sample_cap(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, _subset, **_kwargs: _FakeRows([_row(1, "A"), _row(1, "B")]),
    )

    dataset = EnglishDialectsDataset(cache_dir=tmp_path, subsets=("irish_male", "welsh_female"), num_samples=3)

    assert len(dataset) == 3
    dialects = [dataset[index].dialect for index in range(3)]
    assert set(dialects) == {"irish", "welsh"}
    assert sorted(dialects.count(dialect) for dialect in set(dialects)) == [1, 2]
    with pytest.raises(IndexError):
        _ = dataset[3]


def test_dataset_rejects_unknown_subset(tmp_path):
    with pytest.raises(ValueError, match="Unknown English Dialects subsets"):
        EnglishDialectsDataset(cache_dir=tmp_path, subsets=("invented_male",))


def test_balanced_subset_round_robins_speakers(monkeypatch, tmp_path):
    rows = _FakeRows(
        [
            _row(1, "S1-A"),
            _row(1, "S1-B"),
            _row(1, "S1-C"),
            _row(2, "S2-A"),
            _row(2, "S2-B"),
        ]
    )
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, _subset, **_kwargs: rows,
    )

    dataset = EnglishDialectsDataset(cache_dir=tmp_path, subsets=("irish_male",), samples_per_group=4)

    assert len(dataset) == 4
    assert [dataset[index].line_id for index in range(4)] == ["S1-A", "S2-A", "S1-B", "S2-B"]


def test_balanced_subset_cannot_be_combined_with_global_cap(tmp_path):
    with pytest.raises(ValueError, match="either samples_per_group or num_samples"):
        EnglishDialectsDataset(cache_dir=tmp_path, subsets=("irish_male",), num_samples=10, samples_per_group=5)


@pytest.mark.parametrize("override", [False, True])
def test_dataset_uses_matching_cache_layout_for_default_and_override(monkeypatch, tmp_path, override):
    calls = []

    def fake_load_dataset(_name, subset, **kwargs):
        calls.append((subset, kwargs))
        return _FakeRows([_row(1, "A")])

    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        fake_load_dataset,
    )
    configured_dir = tmp_path / "configured" if override else None
    cache_dir = configured_dir if override else tmp_path / "english_dialects"

    dataset = EnglishDialectsSource(configured_dir).load()

    assert dataset.cache_dir == cache_dir
    assert dataset.raw_cache_dir == cache_dir / "raw"
    assert dataset.raw_cache_dir.is_dir()
    assert dataset.processed_cache_dir == cache_dir / "processed" / "mono_mp3_v1"
    assert dataset.processed_cache_dir.is_dir()
    assert calls == [(subset, {"split": "train", "cache_dir": str(cache_dir / "raw")}) for subset in ALL_SUBSETS]


def test_cloud_config_samples_and_reports_every_published_group(tmp_path, monkeypatch):
    config_path = WORKDIR / "configs" / "english_dialects_cloud_test.yaml"
    config = yaml.safe_load(config_path.read_text())
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, subset, **_kwargs: _FakeRows([_row(1, f"{subset}-1"), _row(2, f"{subset}-2")]),
    )
    dataset = load_benchmark_dataset(
        config["num_samples"],
        dataset_name=config["dataset"],
        samples_per_group=config["samples_per_group"],
        input_dir=tmp_path / "cache",
    )
    assert len(dataset) == len(ALL_SUBSETS)
    assert {f"{dataset[index].dialect}_{dataset[index].gender}" for index in range(len(dataset))} == set(ALL_SUBSETS)
    results = run_engines_parallel(
        [FakeAdapter("test", "hello")],
        list(range(len(dataset))),
        dataset=dataset,
        wav_write_fn=lambda sample, _index: sample.audio.path,
        duration_fn=lambda _path: 1.0,
        run_id="test",
        timestamp="test",
        dataset_version=dataset.dataset_version,
        dataset_split=dataset.dataset_split,
        max_workers=config["max_workers"],
    )
    output = tmp_path / "results.json"
    save_results(results, output)
    groups = json.loads(output.read_text())["wer_by_group"]["test"]
    assert set(groups) == set(ALL_SUBSETS)
    assert all(group["n_examples"] == 1 for group in groups.values())


@pytest.mark.parametrize("budget", [2, 11, 14])
def test_global_budget_is_distributed_across_groups(monkeypatch, budget, tmp_path):
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, subset, **_kwargs: _FakeRows([_row(index, f"{subset}-{index}") for index in range(4)]),
    )
    dataset = EnglishDialectsDataset(cache_dir=tmp_path, num_samples=budget)
    counts = Counter(f"{dataset[index].dialect}_{dataset[index].gender}" for index in range(len(dataset)))
    assert len(dataset) == budget
    assert len(counts) == min(budget, len(ALL_SUBSETS))
    assert max(counts.values()) - min(counts.values()) <= 1
    assert len({dataset[index].line_id for index in range(len(dataset))}) == budget


def test_global_sampling_redistributes_budget_from_empty_and_exhausted_groups(monkeypatch, tmp_path):
    rows = {
        "irish_male": _FakeRows([]),
        "welsh_female": _FakeRows([_row(1, "W")]),
        "scottish_male": _FakeRows([_row(1, "S1"), _row(1, "S2"), _row(2, "S3")]),
    }
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, subset, **_kwargs: rows[subset],
    )
    dataset = EnglishDialectsDataset(cache_dir=tmp_path, subsets=tuple(rows), num_samples=10)
    assert len(dataset) == 4
    assert [dataset[index].line_id for index in range(4)] == ["W", "S1", "S3", "S2"]


@pytest.mark.parametrize("num_samples", [0, -1])
def test_global_sampling_rejects_nonpositive_budget(num_samples, tmp_path):
    with pytest.raises(ValueError, match="num_samples must be greater than zero"):
        EnglishDialectsDataset(cache_dir=tmp_path, num_samples=num_samples)


def test_small_global_budget_is_reproducible_and_independent_of_subset_order(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, subset, **_kwargs: _FakeRows([_row(1, f"{subset}-1"), _row(2, f"{subset}-2")]),
    )

    def selected_groups(subsets):
        dataset = EnglishDialectsDataset(cache_dir=tmp_path, subsets=subsets, num_samples=2)
        return {f"{dataset[index].dialect}_{dataset[index].gender}" for index in range(len(dataset))}

    selected = selected_groups(ALL_SUBSETS)
    assert len(selected) == 2
    assert selected == selected_groups(ALL_SUBSETS)
    assert selected == selected_groups(tuple(reversed(ALL_SUBSETS)))
    assert selected != set(ALL_SUBSETS[:2])


def test_processed_audio_cache_reuses_source_identity_across_sampling(tmp_path, monkeypatch):
    rows = {subset: _FakeRows([_row(1, "A"), _row(2, "B")]) for subset in ("irish_male", "welsh_female")}
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda _name, subset, **_kwargs: rows[subset],
    )
    convert = Mock(side_effect=shutil.copyfile)
    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", convert)
    dataset = EnglishDialectsDataset(subsets=tuple(rows), cache_dir=tmp_path)
    first = dataset[2]
    assert first.audio.path.endswith("welsh_female/000000.mp3")
    assert first.audio.path != dataset[0].audio.path
    assert convert.call_count == 2

    sampled = EnglishDialectsDataset(subsets=("welsh_female",), samples_per_group=1, cache_dir=tmp_path)
    cached = sampled[0]
    assert cached.audio.path == first.audio.path
    np.testing.assert_array_equal(cached.audio.array, first.audio.array)
    assert convert.call_count == 2


def test_cached_sample_uses_actual_mp3_rate_after_ffmpeg_resampling(tmp_path, monkeypatch):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg and ffprobe are required")
    source_rate = 50000
    row = _row(1, "line")
    row["audio"] = {
        "array": 0.2 * np.sin(2 * np.pi * 440 * np.arange(source_rate) / source_rate),
        "sampling_rate": source_rate,
        "path": "",
    }
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda *_args, **_kwargs: _FakeRows([row]),
    )
    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", convert_to_mp3)
    dataset = EnglishDialectsDataset(subsets=("irish_male",), cache_dir=tmp_path)
    first = dataset[0]
    cached = dataset[0]
    file_info = soundfile.info(first.audio.path)
    assert file_info.samplerate != source_rate
    assert first.audio.sampling_rate == file_info.samplerate
    assert cached.audio.sampling_rate == file_info.samplerate
    assert len(first.audio.array) / first.audio.sampling_rate == pytest.approx(1.0, abs=0.01)
    np.testing.assert_array_equal(cached.audio.array, first.audio.array)


def test_processed_cache_hit_does_not_access_source_audio(tmp_path, monkeypatch):
    row = _row(1, "A")
    monkeypatch.setattr(
        "evals.transcription.src.core.english_dialects.english_dialects_dataset.load_dataset",
        lambda *_args, **_kwargs: _FakeRows([row]),
    )
    dataset = EnglishDialectsDataset(subsets=("irish_male",), cache_dir=tmp_path)
    first = dataset[0]
    row.pop("audio")  # Any second source audio access fails; metadata remains available.
    cached = dataset[0]
    assert cached.text == first.text
    np.testing.assert_array_equal(cached.audio.array, first.audio.array)
