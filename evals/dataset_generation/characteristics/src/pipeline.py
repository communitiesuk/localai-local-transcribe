import asyncio
import logging
from pathlib import Path

from common.llm.client import create_chatbot
from evals.dataset_generation.characteristics.src.chunker import (
    build_chunks,
    deduplicate_characteristics,
    process_chunk_parallel,
)
from evals.dataset_generation.characteristics.src.schema import (
    CharacteristicDetection,
    EvalsConfig,
    ExtractionMetadata,
    ProcessedFileResult,
)
from evals.dataset_generation.characteristics.src.transcript_loader import load_transcript

logger = logging.getLogger(__name__)


async def process_file(file_path: Path, config: EvalsConfig, root_dir: Path) -> ProcessedFileResult:
    """Processes a single transcript file, extracting characteristics in chunks."""
    template_name = Path(config.prompts.agent_base_template).stem
    model_name = config.model.model

    logger.info("Processing %s using model '%s'", file_path.name, model_name)

    transcript = load_transcript(file_path)
    chatbot = create_chatbot(
        model_type=config.model.provider,
        model_name=config.model.model,
        temperature=config.model.temperature,
    )

    all_detected_characteristics: list[CharacteristicDetection] = []
    failed_chunks: list[int] = []
    chunks = build_chunks(transcript, config.chunking.chunk_size_chars, config.chunking.overlap_chars)

    base_path = root_dir / config.prompts.agent_base_template
    for idx, (chunk_text, offset) in enumerate(chunks):
        logger.info("  -> Sending Chunk %d of %d to Azure...", idx + 1, len(chunks))
        try:
            detected = await process_chunk_parallel(chunk_text, offset, base_path, chatbot)
            all_detected_characteristics.extend(detected)
            logger.info("     Found %d characteristics in chunk %d", len(detected), idx + 1)
        except (ValueError, RuntimeError, ConnectionError, TimeoutError) as e:
            failed_chunks.append(idx + 1)
            logger.error("     Failed on chunk %d: %s", idx + 1, e)
        if idx < len(chunks) - 1:
            await asyncio.sleep(2)

    metadata = ExtractionMetadata(
        model_used=model_name,
        prompt_version=template_name,
        total_chunks_processed=len(chunks),
        failed_chunks=failed_chunks,
    )
    return ProcessedFileResult(
        version="1.0",
        detected_characteristics=deduplicate_characteristics(all_detected_characteristics),
        metadata=metadata,
    )
