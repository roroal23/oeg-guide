from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from .structures import ExperimentRecord

logger = logging.getLogger("benchmark")

async def writer_task(queue: asyncio.Queue[ExperimentRecord | None], file_path: Path) -> tuple[int, int]:
    """Tarea asyncio dedicada a la escritura de registros"""
    written = 0
    errors = 0

    with open(file_path, "a", encoding = "utf-8") as json_file:
        while True:
            record: ExperimentRecord | None = await queue.get()

            if record is None: #Sentinel, fin del experimento
                queue.task_done()
                break

            try:
                await _write_jsonl(json_file, record)
                written += 1
            except Exception as e:
                logger.error(
                    "Error escribiendo registro %d: %s", record.record_id, e
                )
                errors += 1
            finally:
                queue.task_done()
    logger.info("Writer finalizado: %d escrituras exitosas, %d errores", written, errors)
    return written, errors

async def _write_jsonl(file, record: ExperimentRecord):
    """Escribe el registro como linea JSON en el fichero JSONL"""
    json_line = json.dumps(record.to_jsonl_dict(), ensure_ascii = False) + "\n"

    def _append():
        file.write(json_line)
        file.flush() #Garantizar escritura

    await asyncio.to_thread(_append)
