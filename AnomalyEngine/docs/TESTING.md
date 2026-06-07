# Running Tests

This project uses pytest for unit and integration tests. Tests live under the `tests/` directory.

Quick commands (from project root):

1. Activate your virtual environment (if not already active):

```bash
source venv/bin/activate
```

2. Install test requirements (if needed):

```bash
pip install -r requirements.txt
# or install pytest only
pip install pytest
```

3. Run the full test suite:

```bash
python -m pytest -q
```

4. Run unit tests only:

```bash
python -m pytest tests/unit -q
```

5. Run a single test file:

```bash
python -m pytest tests/unit/test_components.py -q
```

Notes:
- Tests may use the same virtual environment as the app. Ensure dependencies (pandas, numpy, scikit-learn, etc.) are installed.
- CI should run `python -m pytest -q` on PRs to validate changes.
