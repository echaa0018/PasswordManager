import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from server.app import app

if __name__ == "__main__":
    app.run(debug=True)