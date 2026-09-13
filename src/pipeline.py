from __future__ import annotations

from dataclasses import dataclass
from auth import Account


@dataclass
class ContentPipelineServices:
    def owner_gate(self, account: Account) -> None:
        if not account:
            return
