"""Registry of monitor strategies by name, used by orchestration to run the configured sweep."""

from __future__ import annotations

from . import full_review, spot_check, streaming

STRATEGIES = {
    full_review.NAME: full_review.run,
    spot_check.NAME: spot_check.run,
    streaming.NAME: streaming.run,
}
