import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
from server import ack, extract_frames, frame, worklist_from_orm

ORM = "MSH|^~\\&|EHR|HOSPITAL|RIS|RADIOLOGY|20261107110000||ORM^O01|ORM-MWL-001|P|2.5.1\rPID|1||PAT-MWL-1001^^^HOSPITAL^MR||SYNTHETIC^PATIENT\rORC|NW|ORD-MWL-1001\rOBR|1|ORD-MWL-1001|ACC-MWL-1001|CTCHEST^CT Chest without contrast\r"

class MappingTest(unittest.TestCase):
    def test_hl7_to_worklist_mapping(self):
        payload, result = worklist_from_orm(ORM)
        tags = payload["Tags"]
        self.assertTrue(result.accepted)
        self.assertEqual(tags["PatientID"], "PAT-MWL-1001")
        self.assertEqual(tags["AccessionNumber"], "ACC-MWL-1001")
        self.assertEqual(tags["RequestedProcedureDescription"], "CT Chest without contrast")
        self.assertEqual(tags["ScheduledProcedureStepSequence"][0]["Modality"], "CT")
        self.assertRegex(tags["ScheduledProcedureStepSequence"][0]["ScheduledProcedureStepStartDate"], r"^\d{8}$")

    def test_rejects_missing_patient_id(self):
        _, result = worklist_from_orm(ORM.replace("PAT-MWL-1001^^^HOSPITAL^MR", ""))
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "Missing PID-3 PatientID")
        self.assertIn("MSA|AE|ORM-MWL-001", ack(result))
        self.assertIn("ACK^O01^ACK", ack(result))

    def test_reassembles_fragmented_mllp_input(self):
        framed = frame(ORM)
        messages, remainder = extract_frames(framed[:-2])
        self.assertEqual(messages, [])
        messages, remainder = extract_frames(remainder + framed[-2:])
        self.assertEqual(messages, [ORM])
        self.assertEqual(remainder, b"")

