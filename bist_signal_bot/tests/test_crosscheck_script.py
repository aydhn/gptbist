"""scripts/crosscheck_cpcv_skfolio.py skfolio yokken 0 ile cikmali."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_exits_zero_without_skfolio():
    code = (
        "import sys, runpy; sys.modules['skfolio'] = None; "
        "sys.modules['skfolio.model_selection'] = None; "
        "sys.argv = ['x']; "
        "runpy.run_path('scripts/crosscheck_cpcv_skfolio.py', run_name='__main__')"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                       env={**__import__('os').environ, "PYTHONPATH": str(ROOT)})
    assert r.returncode == 0, r.stderr
    assert "skfolio kurulu değil" in r.stdout or "skfolio kurulu degil" in r.stdout
