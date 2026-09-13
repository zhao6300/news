from __future__ import annotations

from typing import Sequence

from scaffold import PlatformExtension


class PlatformServiceInterface:
    def get_extension(self, slug: str) -> PlatformExtension:
        raise NotImplementedError

    def get_extensions(self) -> Sequence[PlatformExtension]:
        raise NotImplementedError


class InMemoryPlatformService(PlatformServiceInterface):
    def __init__(self, extensions: Sequence[PlatformExtension]) -> None:
        self.extensions = list(extensions)

    def get_extension(self, slug: str) -> PlatformExtension:
        for extension in self.extensions:
            if extension.slug == slug:
                return extension
        raise KeyError(slug)

    def get_extensions(self) -> Sequence[PlatformExtension]:
        return self.extensions
