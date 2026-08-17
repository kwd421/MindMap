from __future__ import annotations

from dataclasses import replace

from .physical import PhysicalFaultCase
from .physical_fixtures import all_physical_cases as _raw_cases


def all_physical_cases() -> tuple[PhysicalFaultCase, ...]:
    """Return the fixed physical suite with valid-but-stale projection states.

    P02 removes both the seal and its later unseal from the stale projection,
    avoiding an intrinsically invalid standalone unseal history.

    P09 keeps the projection at the clean idempotent state while the journal
    contains a duplicate replay. The external journal commitment is the
    intended witness; the canonical ledger need not accept duplicate IDs.
    """

    output: list[PhysicalFaultCase] = []
    for case in _raw_cases():
        if case.case_id == "P02":
            projection = tuple(
                event
                for event in case.clean_events
                if event.event_id not in {"F07.seal", "F07.unseal"}
            )
            case = replace(case, faulty_projection_events=projection)
        elif case.case_id == "P09":
            case = replace(case, faulty_projection_events=case.clean_events)
        output.append(case)
    return tuple(output)
