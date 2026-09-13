from extensions.builtin import builtin_collections
from scaffold import CategoryGroup


def main() -> None:
    extensions = builtin_collections()
    if not extensions:
        raise RuntimeError("The platform must load at least one extension.")
    print(f"Loaded {len(extensions[0].entries)} articles across {len(CategoryGroup)} categories.")
