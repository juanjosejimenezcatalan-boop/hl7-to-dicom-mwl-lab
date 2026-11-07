#!/usr/bin/env python3
"""Send a synthetic ORM^O01 through the lab's MLLP bridge."""
import argparse, socket
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("message", type=Path)
parser.add_argument("--port", type=int, default=2577)
args = parser.parse_args()
with socket.create_connection(("127.0.0.1", args.port), timeout=5) as client:
    client.sendall(b"\x0b" + args.message.read_bytes() + b"\x1c\x0d")
    response = client.recv(4096)
print(response.removeprefix(b"\x0b").removesuffix(b"\x1c\x0d").decode().replace("\r", "\n"), end="")

