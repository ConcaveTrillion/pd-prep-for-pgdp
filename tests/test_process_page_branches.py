"""Cover the conditional branches in `core.pipeline.process_page`.

The default-cfg test in test_process_page.py walks the happy path with
all toggles off. This file exercises:
  - corrupt source bytes raise a clear ValueError,
  - `initial_crop` overrides `initial_crop_all`,
  - `threshold_level` overrides Otsu,
  - `white_space_additional` adds padding,
  - `deskew_before_crop` / `deskew_after_crop` rotate the image,
  - `do_morph` runs the morph-fill step.
"""

from __future__ import annotations

import numpy as np
import pytest

from pd_prep_for_pgdp.core.models import (
    AlignmentOverride,
    PageType,
    ResolvedPageConfig,
)
from pd_prep_for_pgdp.core.pipeline.process_page import process_page_cpu


def _cfg(**overrides) -> ResolvedPageConfig:
    base = dict(
        text_threshold=140,
        page_h_w_ratio=1.65,
        fuzzy_pct=0.02,
        pixel_count_columns=150,
        pixel_count_rows=75,
        ocr_bbox_edge_min_words=5,
        ocr_engine="doctr",
        ocr_model_key=None,
        ocr_dpi=150,
        initial_crop_all=(0, 0, 0, 0),
        ocr_crop=(0, 0, 0, 0),
        page_type=PageType.normal,
        alignment=AlignmentOverride.default,
        initial_crop=None,
        white_space_additional=None,
        threshold_level=None,
        skip_auto_deskew=True,
        deskew_before_crop=None,
        deskew_after_crop=None,
        do_morph=False,
        skip_denoise=False,
        use_ocr_bbox_edge=False,
        rotated_standard=False,
        single_dimension_rescale=False,
    )
    base.update(overrides)
    return ResolvedPageConfig(**base)


def _png_with_text(h: int = 1200, w: int = 800) -> bytes:
    cv2 = pytest.importorskip("cv2")
    img = np.full((h, w, 3), 255, dtype=np.uint8)
    cv2.rectangle(img, (100, 100), (w - 100, h - 100), (0, 0, 0), -1)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return bytes(buf.tobytes())


def test_corrupt_source_bytes_raise_value_error() -> None:
    pytest.importorskip("cv2")
    with pytest.raises(ValueError, match="could not decode"):
        process_page_cpu(b"not an image", _cfg())


def test_initial_crop_override_runs_crop_branch() -> None:
    pytest.importorskip("cv2")
    src = _png_with_text()
    out = process_page_cpu(src, _cfg(initial_crop=(20, 20, 20, 20)))
    assert out.height > 0 and out.width > 0


def test_explicit_threshold_level_branch() -> None:
    pytest.importorskip("cv2")
    src = _png_with_text()
    out = process_page_cpu(src, _cfg(threshold_level=120))
    assert out.height > 0


def test_white_space_additional_padding_branch() -> None:
    pytest.importorskip("cv2")
    src = _png_with_text()
    out = process_page_cpu(src, _cfg(white_space_additional=(0.05, 0.05, 0.05, 0.05)))
    assert out.height > 0 and out.width > 0


def test_deskew_before_crop_branch() -> None:
    pytest.importorskip("cv2")
    src = _png_with_text()
    out = process_page_cpu(src, _cfg(deskew_before_crop=0.5))
    assert out.height > 0


def test_deskew_after_crop_branch() -> None:
    pytest.importorskip("cv2")
    src = _png_with_text()
    out = process_page_cpu(src, _cfg(deskew_after_crop=-0.3))
    assert out.height > 0


def test_do_morph_branch() -> None:
    pytest.importorskip("cv2")
    src = _png_with_text()
    out = process_page_cpu(src, _cfg(do_morph=True))
    assert out.height > 0


def test_auto_deskew_branch_runs_when_default_alignment_and_no_skip() -> None:
    """With skip_auto_deskew=False and default alignment / no rescale /
    no rotate, the pipeline runs auto_deskew (the else-branch in 4k)."""
    pytest.importorskip("cv2")
    src = _png_with_text()
    # skip_auto_deskew=False is the only override needed — all other toggles
    # default to "auto-deskew applies".
    out = process_page_cpu(src, _cfg(skip_auto_deskew=False))
    assert out.height > 0 and out.width > 0
