"""Synthetic ORM^O01-to-Orthanc Worklist bridge. Not for clinical use."""
from __future__ import annotations
import argparse, json, logging, os, socketserver, time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.request import Request, urlopen

VT, FS_CR = b"\x0b", b"\x1c\x0d"

@dataclass(frozen=True)
class Result:
    accepted: bool
    control_id: str
    reason: str = ""

def segments(message: str) -> dict[str, list[str]]:
    result = {}
    for line in message.replace("\n", "\r").split("\r"):
        if line:
            fields = line.split("|")
            result.setdefault(fields[0], fields)
    return result

def get(s: dict[str, list[str]], name: str, n: int) -> str:
    return s.get(name, [])[n] if len(s.get(name, [])) > n else ""

def worklist_from_orm(message: str) -> tuple[dict, Result]:
    s = segments(message)
    control_id = get(s, "MSH", 9)
    if get(s, "MSH", 8) != "ORM^O01":
        return {}, Result(False, control_id, "Expected MSH-9 ORM^O01")
    patient_id = get(s, "PID", 3).split("^")[0]
    accession = get(s, "OBR", 3).split("^")[0]
    procedure = get(s, "OBR", 4)
    placer_order = get(s, "ORC", 2).split("^")[0]
    if not patient_id:
        return {}, Result(False, control_id, "Missing PID-3 PatientID")
    if not placer_order or not accession or not procedure:
        return {}, Result(False, control_id, "Missing ORC-2, OBR-3, or OBR-4")
    description = procedure.split("^", 1)[1] if "^" in procedure else procedure
    scheduled = datetime.now(timezone.utc)
    tags = {
        "PatientID": patient_id,
        "PatientName": get(s, "PID", 5) or "SYNTHETIC^PATIENT",
        "AccessionNumber": accession,
        "RequestedProcedureID": placer_order,
        "RequestedProcedureDescription": description,
        "ScheduledProcedureStepSequence": [{
            "ScheduledStationAETitle": "CT_SIM",
            "ScheduledProcedureStepID": placer_order,
            "ScheduledProcedureStepDescription": description,
            "ScheduledProcedureStepStartDate": scheduled.strftime("%Y%m%d"),
            "ScheduledProcedureStepStartTime": scheduled.strftime("%H%M%S"),
            "Modality": "CT"
        }]
    }
    return {"Tags": tags}, Result(True, control_id)

def ack(result: Result) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S+0000")
    code = "AA" if result.accepted else "AE"
    lines = [f"MSH|^~\\&|MWL_BRIDGE|RADIOLOGY|SENDER|HOSPITAL|{timestamp}||ACK^O01^ACK|ACK-{result.control_id}|P|2.5.1", f"MSA|{code}|{result.control_id}"]
    if not result.accepted:
        lines.append(f"ERR|||{result.reason}")
    return "\r".join(lines) + "\r"

def frame(message: str) -> bytes:
    return VT + message.encode() + FS_CR

def extract_frames(buffer: bytes) -> tuple[list[str], bytes]:
    """Return all complete MLLP frames and retain an incomplete frame."""
    messages = []
    while True:
        start = buffer.find(VT)
        if start < 0:
            return messages, b""
        end = buffer.find(FS_CR, start + 1)
        if end < 0:
            return messages, buffer[start:]
        messages.append(buffer[start + 1:end].decode(errors="replace"))
        buffer = buffer[end + len(FS_CR):]

def post_worklist(payload: dict) -> None:
    data = json.dumps(payload).encode()
    request = Request(os.environ.get("ORTHANC_URL", "http://127.0.0.1:8042") + "/worklists/create", data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=5) as response:
        if response.status not in (200, 201):
            raise RuntimeError(f"Orthanc returned HTTP {response.status}")

class Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        buffer = b""
        while chunk := self.request.recv(65536):
            buffer += chunk
            messages, buffer = extract_frames(buffer)
            for message in messages:
                payload, result = worklist_from_orm(message)
                if result.accepted:
                    try:
                        post_worklist(payload)
                    except Exception as exc:
                        result = Result(False, result.control_id, f"Worklist creation failed: {exc}")
                logging.info("%s control_id=%s reason=%s", "ACCEPTED" if result.accepted else "REJECTED", result.control_id, result.reason or "-")
                self.request.sendall(frame(ack(result)))

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class UTCFormatter(logging.Formatter):
    converter = time.gmtime

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", type=int, default=2575); p.add_argument("--log", default="bridge.log"); a = p.parse_args()
    handler = logging.FileHandler(a.log); handler.setFormatter(UTCFormatter("%(asctime)sZ %(levelname)s %(message)s")); logging.basicConfig(level=logging.INFO, handlers=[handler])
    with Server((a.host, a.port), Handler) as server: server.serve_forever()

if __name__ == "__main__": main()

