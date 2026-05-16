import sys
from pathlib import Path

# audit_meeting.py imports classify from the same directory (python/).
# Adding python/ here ensures both modules resolve correctly during test collection.
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
