import subprocess
import sys
from pathlib import Path

PROTO_DIR = Path(__file__).parent.parent.parent / "proto"
OUT_DIR = Path(__file__).parent.parent / "app" / "grpc"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    proto_files = list(PROTO_DIR.glob("*.proto"))
    if not proto_files:
        print("No .proto files found in", PROTO_DIR)
        sys.exit(1)
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"--proto_path={PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        *[str(f) for f in proto_files],
    ]
    subprocess.check_call(cmd)
    print("Generated gRPC code in", OUT_DIR)


if __name__ == "__main__":
    main()
