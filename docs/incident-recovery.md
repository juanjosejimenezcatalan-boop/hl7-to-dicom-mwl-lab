# Incident and recovery records

All cases below use synthetic messages and identifiers. The captured
[validation evidence](validation.md) is an integration complement to the unit
tests; it is not fabricated output.

## Incorrect called AE Title

| Field | Record |
| --- | --- |
| Symptom | `findscu` reports `Association Rejected` and `Called AE Title Not Recognized`. |
| Root cause | The CT modality calls `WRONG_AET`, while Orthanc is configured as `ORTHANC_MWL` and checks called AE Titles. |
| Test | Run the wrong-AE command in the README with `-aec WRONG_AET`. |
| Recovery | Restore the called title to `-aec ORTHANC_MWL`. |
| Verification | The CT C-FIND returns a pending match that contains `PatientID`, `AccessionNumber`, and modality `CT`. |

## No matching modality worklist entry

| Field | Record |
| --- | --- |
| Symptom | The C-FIND association succeeds but returns no scheduled procedure. |
| Root cause | The query requests `MR` while the HL7-to-DICOM mapping created a `CT` scheduled procedure. |
| Test | Query `ScheduledProcedureStepSequence.Modality=MR` after submitting the CT ORM fixture. |
| Recovery | Submit the intended synthetic order or query with the matching `CT` modality. |
| Verification | The accepted CT query returns `PAT-MWL-1001` and `ACC-MWL-1001`. |

## Rejected HL7 order

| Field | Record |
| --- | --- |
| Symptom | The MLLP sender receives `MSA|AE` with `ERR|||Missing PID-3 PatientID`. |
| Root cause | The inbound ORM omits the identifier required to construct DICOM `PatientID`. |
| Test | Send `messages/invalid_missing_patient_id.hl7`. |
| Recovery | Correct the source ORM to include synthetic `PID-3`. |
| Verification | Send `messages/orm_o01_ct_chest.hl7`; the bridge returns `ACK^O01^ACK` and the subsequent CT C-FIND finds the created worklist entry. |
