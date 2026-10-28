"""Repository-only Phase 29 release-state verification; never opens a DB."""

import json

from foundation.phase29_publication_evidence import offline_release_state


if __name__ == "__main__":
    print(json.dumps(offline_release_state(), indent=2, sort_keys=True))

