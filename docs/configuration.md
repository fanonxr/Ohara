# Configuration Examples

V1 uses constructor options rather than a full config file. A future release can load these values from `ohara.toml`.

## Scanner

```python
from ohara.context.scanner import RepositoryScanner

scanner = RepositoryScanner(
    include=["*.py", "*.toml", "*.md"],
    exclude=["fixtures", ".generated"],
    max_files=400,
    review_mode="architecture-review",
)
```

`review_mode` controls mode-specific context and excludes. Architecture and startup
readiness runs exclude `.sqlx` metadata by default; security audit runs may include it as
database-shape context while still treating regex matches as triage candidates.

## Storage

```python
from pathlib import Path
from ohara.storage.filesystem import FileSystemStorage

storage = FileSystemStorage(Path(".ohara/reviews"))
```

## ChatGPT Playwright CLI Provider

```python
from pathlib import Path
from ohara.automation.chatgpt import ChatGPTPlaywrightCliProvider

provider = ChatGPTPlaywrightCliProvider(
    command=("playwright-cli",),
    session="ohara-chatgpt",
    profile_dir=Path(".ohara/playwright-cli-profile"),
    headed=True,
)
```

The provider is expected to reuse an authenticated browser session. Run once interactively, sign into ChatGPT, then reuse the same CLI session/profile for later runs.
