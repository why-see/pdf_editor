"""Batch-remove the last page of PDFs without overwriting original files."""
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from tqdm import tqdm

log = logging.getLogger(__name__)

def process_pdf(source: Path, destination: Path) -> bool:
    """Return True when a PDF with two or more pages was processed."""
    try:
        with source.open("rb") as stream:
            reader = PdfReader(stream)
            if len(reader.pages) < 2:
                log.warning("Skipping %s: fewer than two pages", source.name)
                return False
            writer = PdfWriter()
            for page in reader.pages[:-1]:
                writer.add_page(page)
            target = unique_filename(destination)
            # Exclusive creation avoids silently replacing an existing output.
            with target.open("xb") as output:
                writer.write(output)
        log.info("Saved %s", target)
        return True
    except Exception:
        log.exception("Failed to process %s", source.name)
        return False

def unique_filename(path: Path) -> Path:
    candidate = path
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        counter += 1
    return candidate

def remove_last_page(input_folder: str, output_folder: str, workers: int = 4) -> tuple[int, int]:
    source = Path(input_folder).expanduser().resolve()
    destination = Path(output_folder).expanduser().resolve()
    if not source.is_dir():
        raise NotADirectoryError(f"Input folder does not exist: {source}")
    if source == destination:
        raise ValueError("Input and output folders must be different")
    destination.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in source.glob("*.pdf") if p.is_file())
    successes = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_pdf, path, destination / f"edited_{path.name}") for path in files]
        for future in tqdm(as_completed(futures), total=len(futures), desc="PDFs"):
            successes += int(future.result())
    log.info("Finished: %s succeeded, %s skipped or failed", successes, len(files) - successes)
    return successes, len(files) - successes

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_folder", help="Directory of input PDF files")
    parser.add_argument("output_folder", help="Directory for edited files")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 16:
        parser.error("--workers must be between 1 and 16")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        success, failed = remove_last_page(args.input_folder, args.output_folder, args.workers)
        return 1 if failed else 0
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
