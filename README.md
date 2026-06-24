# qhld-data

Shared data layer for QHLD (Qué Hacen Los Diputados). A small Python library that
owns the MongoDB connection, the Pydantic document models, and the repository
functions used to read and write them. It is consumed by **qhld-backend**,
**qhld-tasks**, and **qhld-engine**, which pin a released version of this package.

The package is importable as `tipi_data`:

```python
from tipi_data import db, DoesNotExist
from tipi_data.repositories.topics import Topics

topics = Topics.all()
```

## Requirements

- Python `>=3.12`
- [uv](https://docs.astral.sh/uv/) for dependency management
- A reachable MongoDB (for anything that touches the database)
- Docker (only to run the database-backed tests — see below)

## Install / development

This project uses **uv**. To set up a working environment:

```bash
uv sync                 # create .venv and install runtime + dev dependencies
```

Run any command inside the environment with `uv run`:

```bash
uv run python -c "import tipi_data; print(tipi_data.__name__)"
uv run pytest
```

Manage dependencies with uv (this edits `pyproject.toml` and `uv.lock`):

```bash
uv add <package>            # add a runtime dependency
uv add --dev <package>      # add a dev-only dependency
uv remove <package>         # remove a dependency
```

## Configuration

The MongoDB connection is built at import time from environment variables, with
the defaults defined in `tipi_data/config.py`:

| Variable          | Default   | Notes                                            |
| ----------------- | --------- | ------------------------------------------------ |
| `MONGO_HOST`      | `mongo`   | `mongo` is the docker-compose service hostname.  |
| `MONGO_PORT`      | `27017`   |                                                  |
| `MONGO_USER`      | `qhld`    | Authentication resolves against the `admin` db.  |
| `MONGO_PASSWORD`  | `qhld`    |                                                  |
| `MONGO_DB_NAME`   | `qhlddb`  | The application database.                        |

There is also `MONGO_SKIP_INDEX_INIT`: when set, importing the package does not
create indexes (used so DB-free unit tests can import `tipi_data` offline).

## Running tests

There are two kinds of tests:

- **`tests/unit`** (marker `unit`) — model round-trip tests; **no infrastructure**,
  run anywhere.
- **`tests/integration`** (marker `integration`) — repository and schema tests that
  need MongoDB. They start a **throwaway `mongo` container automatically** (via
  `testcontainers`) and tear it down at the end — no manual setup, no env vars to
  pick.

```bash
uv run pytest                  # everything
uv run pytest -m unit          # no-infra tests only — no Docker required
uv run pytest -m integration   # container-backed tests only
```

Notes:

- **Docker is required** for the integration tier. If Docker is unavailable, those
  tests are skipped rather than failed, so a plain `uv run pytest` stays green
  anywhere.
- The container is published on the fixed host port **`47017`**, so two test runs
  cannot execute concurrently and `pytest-xdist` is not supported.
- **Safety:** the `mongo_db` fixture **drops all collections** before and after
  each test, so the suite must only ever point at a throwaway/test database. A
  guard asserts the database name ends in `_test`; a misconfigured run (e.g.
  pointing at `qhlddb`) fails loudly instead of wiping data.
