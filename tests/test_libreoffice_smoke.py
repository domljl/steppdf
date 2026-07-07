import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(os.getenv("RUN_LIBREOFFICE_SMOKE") != "1", reason="set RUN_LIBREOFFICE_SMOKE=1 to run")
def test_libreoffice_converts_sample_pptx(tmp_path):
    sample = Path("samples/C270 Team 1.pptx")
    if not sample.exists() or not shutil.which("soffice"):
        pytest.skip("sample PPTX or soffice missing")

    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(sample)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert (tmp_path / "C270 Team 1.pdf").exists()
