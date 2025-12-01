import logging
import re
from pathlib import Path
from typing import List, Tuple

from src.storage.backends import StorageBackend, storage_backend

logger = logging.getLogger(__name__)

FILE_BLOCK_PATTERN = re.compile(
    r"# file:\s*(.+?)\s*\n(.*?)(?=(\n# file:|\Z))",
    re.DOTALL | re.MULTILINE,
)


def parse_file_blocks(text: str) -> List[Tuple[str, str]]:
    """Parse '# file: path' blocks from LLM output.

    Returns a list of (relative_path, content).
    """
    logger.debug(f"parse_file_blocks() - starting to parse file blocks from text of length {len(text) if text else 0}")

    if not text:
        logger.debug("parse_file_blocks() - input text is empty, returning empty list")
        return []

    blocks: List[Tuple[str, str]] = []
    match_count = 0

    for match in FILE_BLOCK_PATTERN.finditer(text):
        match_count += 1
        rel_path = match.group(1).strip()
        content = match.group(2)
        # Strip leading newlines
        content = content.lstrip("\n")
        # Strip fenced code if present
        if content.strip().startswith("```"):
            # remove first ```... line
            lines = content.splitlines()
            if lines:
                lines = lines[1:]
            # remove closing ``` if present at end
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).lstrip("\n")

        blocks.append((rel_path, content))
        logger.debug(f"parse_file_blocks() - parsed file block #{match_count}: {rel_path} ({len(content)} chars)")

    logger.info(f"parse_file_blocks() - successfully extracted {match_count} file blocks from LLM output")
    return blocks


def _next_semantic_name(parent: Path, stem: str, suffix: str, approved: bool) -> Path:
    """Decide semantic filename based on existing files and approval status.

    Semantic scheme:
    - If approved: create '<stem>.final<suffix>'.
    - If not approved:
      - If no existing draft/fix file: '<stem>.draft<suffix>'
      - Else: '<stem>.fixN<suffix>' with N incremented.
    """
    logger.debug(
        f"_next_semantic_name() - determining semantic name for stem={stem}, suffix={suffix}, "
        f"approved={approved}, parent={parent}"
    )

    # Normalise suffix
    if not suffix:
        suffix = ""
    draft = parent / f"{stem}.draft{suffix}"
    final = parent / f"{stem}.final{suffix}"

    if approved:
        # Never overwrite existing final; if exists, just return it.
        if final.exists():
            logger.debug(f"_next_semantic_name() - approved mode, final file already exists: {final}")
            return final
        logger.debug(f"_next_semantic_name() - approved mode, creating new final filename: {final}")
        return final

    # Not approved: choose draft or next fix
    if not draft.exists():
        logger.debug(f"_next_semantic_name() - not approved, no draft exists, using: {draft}")
        return draft

    logger.debug(f"_next_semantic_name() - not approved, draft exists, searching for fix files")
    # Find existing fix files
    existing_fix_indices = []
    for p in parent.glob(f"{stem}.fix*{suffix}"):
        name = p.stem  # e.g., 'main.fix2'
        if ".fix" in name:
            try:
                idx = int(name.split(".fix", 1)[1])
                existing_fix_indices.append(idx)
            except ValueError:
                logger.debug(f"_next_semantic_name() - could not parse fix index from {name}")
                continue

    next_idx = (max(existing_fix_indices) + 1) if existing_fix_indices else 1
    fix_path = parent / f"{stem}.fix{next_idx}{suffix}"
    logger.debug(f"_next_semantic_name() - determined next fix file: {fix_path} (fix index: {next_idx})")
    return fix_path


async def write_artifact_files(
        run_output_dir: Path,
        backend_code: str,
        frontend_code: str,
        tests_code: str,
        devops_code: str,
        approved: bool,
        storage: StorageBackend = storage_backend
) -> None:
    """Write artifacts under run_output_dir based on LLM outputs.

    Respects '# file: path' markers and uses semantic filenames (draft/fix/final).
    """
    logger.info(
        f"write_artifact_files() - starting artifact write, output_dir={run_output_dir}, "
        f"approved={approved}, num_code_categories={'backend' if backend_code else 0 + 'frontend' if frontend_code else 0},"
        f"using storage={storage.__class__.__name__}"
    )

    try:
        run_output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"write_artifact_files() - ensured output directory exists: {run_output_dir}")
    except Exception as e:
        logger.error(
            f"write_artifact_files() - failed to create output directory {run_output_dir}: {e}",
            exc_info=True
        )
        raise

    async def _write_category(code_text: str, category_name: str):
        """Write code artifacts for a specific category (backend, frontend, tests, devops)."""
        logger.debug(
            f"write_artifact_files._write_category() - processing {category_name} code ({len(code_text)} chars)")

        for rel_path, content in parse_file_blocks(code_text):
            try:
                target = run_output_dir / rel_path
                parent = target.parent
                parent.mkdir(parents=True, exist_ok=True)

                # Ensure package structure by auto-creating __init__.py for every folder up to output root
                current = parent
                while str(current).startswith(str(run_output_dir)):
                    init_file = current / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text("", encoding="utf-8")
                        logger.info(f"Created package file: {init_file}")
                    current = current.parent

                stem = target.stem
                suffix = target.suffix
                semantic_path = _next_semantic_name(parent, stem, suffix, approved)
                await storage.write_file(str(semantic_path), content)
                semantic_path.write_text(content, encoding="utf-8")
                logger.info(
                    f"write_artifact_files._write_category() - successfully wrote {category_name} "
                    f"artifact to {semantic_path} ({len(content)} chars)"
                )
                # ALSO write/update canonical file without suffix (so imports work)
                canonical_path = parent / f"{stem}{suffix}"
                await storage.write_file(str(canonical_path), content)
                canonical_path.write_text(content, encoding="utf-8")
                logger.info(
                    f"write_artifact_files._write_category() - updated canonical runnable file: {canonical_path}"
                )
            except Exception as e:
                logger.error(
                    f"write_artifact_files._write_category() - failed to write artifact {rel_path} "
                    f"in {category_name} category: {e}",
                    exc_info=True
                )
                raise

    try:
        if backend_code:
            logger.debug("write_artifact_files() - processing backend code")
            await _write_category(backend_code, "backend")
        if frontend_code:
            logger.debug("write_artifact_files() - processing frontend code")
            await _write_category(frontend_code, "frontend")
        if tests_code:
            logger.debug("write_artifact_files() - processing tests code")
            await _write_category(tests_code, "tests")
        if devops_code:
            logger.debug("write_artifact_files() - processing devops code")
            await _write_category(devops_code, "devops")

        logger.info("write_artifact_files() - successfully completed artifact write operation")
    except Exception as e:
        logger.error(f"write_artifact_files() - artifact write operation failed: {e}", exc_info=True)
        raise
