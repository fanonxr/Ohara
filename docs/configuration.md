# Configuration Examples

V1 uses constructor options rather than a full config file. A future release can load these values from `ohara.toml`.

## Scanner

```python
from ohara.context.scanner import RepositoryScanner

scanner = RepositoryScanner(
    include=["*.py", "*.toml", "*.md"],
    exclude=["fixtures", ".generated"],
    max_files=400,
)
```

## Storage

```python
from pathlib import Path
from ohara.storage.filesystem import FileSystemStorage

storage = FileSystemStorage(Path(".ohara/reviews"))
```

## ChatGPT Provider

```python
from pathlib import Path
from ohara.automation.chatgpt import ChatGPTPlaywrightProvider

provider = ChatGPTPlaywrightProvider(
    user_data_dir=Path(".ohara/browser-profile"),
    headless=False,
)
```

The provider is expected to reuse an authenticated browser session. Run once interactively, sign into ChatGPT, then reuse the same profile for later runs.
