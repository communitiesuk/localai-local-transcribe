# ADR-020: FFMPEG Processing

## Status

Proposed

Date of decision: 2026-03-05

## Context and Problem Statement

### Codec

Local Transcribe uses FFmpeg to process audio files. What is the optimal codec (and codec parameters) that minimise CPU time, file size, and maximises transcription quality?

### Speed

Additionally, using FFmpeg to speed up audio can save on transcription costs. What happens to transcription quality when audio is sped up and what impact does this have on costs?

## Considered Options

### Codec

WAV, FLAC, MP3, AAC, Opus, and MP4. Various codec parameters - see `docmentation/experiments/ffmpeg-varied-codecs.md` for full exploration.

### Speed

Speeds of 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.7, 1.9 - see `documentation/experiments/sped-transcription.md` for full exploration.

## Decision Outcome

### Codec

Optimising for CPU time and file size is not a priority - costs associated with these parameters are minimal. Therefore, use whichever codec that results in the highest transcription quality.

This is MP3, sample rate 1600, bitrate 192k, audio channels 1. These parameters are the same as in the source Minute repo.

### Speed

A decision is yet to be made on whether we speed up audio and if so to what speed. This decision will be made as part of a wider cost/benefit evaluation.

## Pros and Cons of the Options

### Codec

Tradeoffs between CPU time, file size, and transcription quality explored in `docmentation/experiments/ffmpeg-varied-codecs.md`.

### Speed

Tradeoffs between transcription costs and transcription quality explored in `docmentation/experiments/sped-transcription.md`.
