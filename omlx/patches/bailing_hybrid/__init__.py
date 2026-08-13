# SPDX-License-Identifier: Apache-2.0
"""Ling 3.0 (bailing_hybrid) support for the pinned mlx-lm dependency.

Provides two MLA implementations selectable via ``bailing_mla_mode`` model
setting:

* ``"auto"`` (default): use upstream ``mlx_lm.models.bailing_hybrid`` when
  available (standard per-head KV cache — faster for short context).
* ``"latent"``: force the vendored module (compressed latent KV cache —
  ~9x smaller MLA cache, faster for long context >4K).

The vendored copy also implements Ling's SwiGLU clamp natively and handles
both original and upstream-sanitized checkpoint weight layouts.

MLX-LM resolves architectures by importing modules under its own namespace.
The selected module is registered there before mlx-lm resolves its classes.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path

from .swiglu_clamp import ensure_swiglu_clamp

logger = logging.getLogger(__name__)

BRANCH_HEAD_SHA = "d719464ff754e65d9dec496ef3fea27bddefd79c"
SOURCE_URL = (
    "https://github.com/scaryrawr/mlx-lm/blob/ling-3.0-flash/"
    "mlx_lm/models/bailing_hybrid.py"
)

_MODULE_NAME = "mlx_lm.models.bailing_hybrid"
_APPLIED = False
_APPLIED_MODE: str | None = None


def _register_vendored() -> None:
    """Register the vendored bailing_hybrid module (latent MLA)."""
    file_path = Path(__file__).parent / "bailing_hybrid_model.py"
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create spec for {_MODULE_NAME} from {file_path}")

    module = importlib.util.module_from_spec(spec)
    module.__package__ = "mlx_lm.models"
    # Replace any prior registration (upstream or stale vendored)
    sys.modules[_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
        models_pkg = importlib.import_module("mlx_lm.models")
        models_pkg.bailing_hybrid = module
    except BaseException:
        if sys.modules.get(_MODULE_NAME) is module:
            sys.modules.pop(_MODULE_NAME)
        raise

    logger.info("Registered vendored %s (latent MLA) from %s", _MODULE_NAME, file_path.name)


def _ensure_upstream() -> None:
    """Ensure upstream bailing_hybrid is importable and registered."""
    module = importlib.import_module(_MODULE_NAME)
    models_pkg = importlib.import_module("mlx_lm.models")
    models_pkg.bailing_hybrid = module


def apply_bailing_hybrid_patch(force_vendored: bool = False) -> bool:
    """Register the appropriate bailing_hybrid module.

    Args:
        force_vendored: If True, use the vendored latent-MLA module
            (long-context optimised KV cache). If False, prefer upstream.

    Returns:
        True if the vendored module was registered, False for upstream.
    """
    global _APPLIED, _APPLIED_MODE
    mode = "latent" if force_vendored else "auto"

    if _APPLIED and _APPLIED_MODE == mode:
        return force_vendored
    if _APPLIED and _APPLIED_MODE != mode:
        # Mode switch: must re-register. Reset state so the next load
        # picks up the new module. The actual swap happens below.
        logger.info(
            "bailing_hybrid MLA mode switch: %s → %s", _APPLIED_MODE, mode
        )
        _APPLIED = False
        _APPLIED_MODE = None

    try:
        importlib.import_module("mlx_lm")
    except ModuleNotFoundError:
        logger.debug("mlx_lm not importable - bailing_hybrid patch skipped")
        return False

    if force_vendored:
        _register_vendored()
    else:
        try:
            _ensure_upstream()
        except ModuleNotFoundError:
            # Upstream lacks bailing_hybrid — fall back to vendored
            logger.info(
                "upstream mlx_lm has no bailing_hybrid; using vendored module"
            )
            _register_vendored()
            force_vendored = True  # report accurately

    # Install SwiGLU clamp on whichever module is live.
    module = importlib.import_module(_MODULE_NAME)
    if ensure_swiglu_clamp(module):
        logger.info("Ling SwiGLU clamp installed on %s", _MODULE_NAME)

    _APPLIED = True
    _APPLIED_MODE = mode

    if force_vendored:
        logger.info(
            "Ling bailing_hybrid vendored module registered "
            "(branch head %s, latent MLA cache)", BRANCH_HEAD_SHA[:8]
        )
    else:
        logger.debug("mlx_lm.models.bailing_hybrid using upstream build")

    return force_vendored


def is_applied() -> bool:
    return _APPLIED


__all__ = [
    "BRANCH_HEAD_SHA",
    "SOURCE_URL",
    "apply_bailing_hybrid_patch",
    "is_applied",
]
