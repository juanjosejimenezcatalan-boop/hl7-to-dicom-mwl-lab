# Validation evidence

All evidence below was generated using the synthetic `ORM^O01` fixture.

## Accepted CT worklist query

After submitting `messages/orm_o01_ct_chest.hl7`, run:

```sh
docker compose --profile tools run --rm mwl-client \
  -v +sr -W -aet CT_SIM -aec ORTHANC_MWL \
  -k "0040,0100[0].0008,0060=CT" \
  -k "0010,0020=" -k "0008,0050=" orthanc-mwl 4242
```

The pending C-FIND response contains:

```text
(0008,0050) SH [ACC-MWL-1001]  AccessionNumber
(0010,0020) LO [PAT-MWL-1001]  PatientID
(0040,0100) SQ ScheduledProcedureStepSequence
  (0008,0060) CS [CT]          Modality
```

## Rejected association: wrong called AE Title

```sh
docker compose --profile tools run --rm mwl-client \
  -v -W -aet CT_SIM -aec WRONG_AET \
  -k "0008,0050=*" orthanc-mwl 4242
```

Expected result:

```text
I: Requesting Association
E: Association Rejected:
E: Result: Rejected Permanent, Source: Service User
E: Reason: Called AE Title Not Recognized
```

Screenshots should include the response or rejection lines above. A container
startup banner alone is not sufficient evidence of either outcome.
