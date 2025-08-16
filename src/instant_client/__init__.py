try:
    from .runtime.core import init, AsyncClient
except (ImportError, ModuleNotFoundError):  # pragma: no cover - optional during codegen
    # Allow importing the package when optional runtime deps (e.g., httpx) are missing.
    # This is useful for running the generator in minimal environments.
    pass
