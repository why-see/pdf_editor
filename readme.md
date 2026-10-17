# PDF last-page remover

Removes the final page from each PDF in a directory. Source documents are never overwritten; output files are saved to a separate folder and receive a numeric suffix when needed.

## Local use

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python pdf_editor.py /path/to/input /path/to/output --workers 4
```

The command exits nonzero if any PDFs fail or are skipped (for example, one-page files). It does not use GitHub Actions.
