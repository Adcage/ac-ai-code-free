import sys
from pathlib import Path

_sys_path_added = False

if not _sys_path_added:
    _grpc_dir = str(Path(__file__).parent)
    if _grpc_dir not in sys.path:
        sys.path.insert(0, _grpc_dir)
    _sys_path_added = True
