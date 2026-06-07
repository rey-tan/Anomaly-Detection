import os
import warnings


def pytest_configure(config):
    # ensure test-only endpoints are enabled when test files rely on them
    os.environ.setdefault("ENV", "development")

    config.addinivalue_line(
        "filterwarnings",
        r"ignore:datetime\.datetime\.utcnow\(\) is deprecated.*:DeprecationWarning",
    )
    config.addinivalue_line(
        "filterwarnings",
        r"ignore:.*`dict` method is deprecated.*:DeprecationWarning",
    )
    config.addinivalue_line(
        "filterwarnings",
        r"ignore:'T' is deprecated.*:FutureWarning",
    )
    config.addinivalue_line(
        "filterwarnings",
        r"ignore:Series\.fillna with 'method' is deprecated.*:FutureWarning",
    )
    config.addinivalue_line(
        "filterwarnings",
        r"ignore:Using `httpx` with `starlette\.testclient` is deprecated.*",
    )
