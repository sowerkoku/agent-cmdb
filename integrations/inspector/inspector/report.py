"""Inspector report — deterministic output of a run.

A report pins everything needed to reproduce the same findings:
dataset_hash, inspector_version, policy_version, generation, and the
parameters used. Any two runs with the same four inputs MUST produce
identical reports — identical findings, severities, falsation blocks.

Writes JSON via to_json(). Never writes to the Knowledge Kernel.
Never modifies the dataset.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Type

from inspector import __version__, __policy_version__
from inspector.kernel_api import KernelAPI, default_api
from inspector.rule import Finding, Rule


@dataclass(frozen=True)
class Report:
    generated_at: str
    inspector_version: str
    policy_version: str
    dataset_hash: str
    generation: int
    parameters: dict
    findings: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "inspector_version": self.inspector_version,
            "policy_version": self.policy_version,
            "dataset_hash": self.dataset_hash,
            "generation": self.generation,
            "parameters": self.parameters,
            "findings": _findings_to_jsonable(self.findings),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def _findings_to_jsonable(findings: Iterable[Finding]) -> list:
    out = []
    for f in findings:
        out.append(asdict(f))
    return out


def run_inspector(
    rules: Iterable[Type[Rule] | Rule],
    *,
    api: KernelAPI | None = None,
    policy: dict | None = None,
    now: datetime | None = None,
) -> Report:
    """Run a set of rules against the Knowledge Kernel via the public API.

    Args:
        rules: Iterable of Rule classes (or instances) to run.
        api: KernelAPI facade. Defaults to a fresh instance exposing
             only public API functions.
        policy: Dict of policy parameters forwarded to each rule.
                The full dict is also pinned in the report.
        now: Override reference clock for reproducibility.
    """
    api = api or default_api()
    now = now or datetime.now(tz=timezone.utc)
    policy = policy or {}
    engine = api.cmdb_engine_info()

    findings: list[Finding] = []
    for rule_obj in rules:
        rule: Rule
        if isinstance(rule_obj, type):
            rule = rule_obj()
        else:
            rule = rule_obj
        # Verify rule consumes only declared public API.
        for fn_name in rule.consumes_api:
            if fn_name not in {n for n in dir(api) if not n.startswith("_")}:
                raise ValueError(
                    f"Rule {rule.id} declares consumes_api={fn_name!r} "
                    f"but this name is not exposed by KernelAPI."
                )
        for f in rule.evaluate(api=api, policy=policy, now=now):
            findings.append(f)

    return Report(
        generated_at=now.isoformat(),
        inspector_version=__version__,
        policy_version=__policy_version__,
        dataset_hash=str(engine.get("dataset_hash")),
        generation=int(engine.get("generation", 0)),
        parameters={"policy": policy, "now": now.isoformat()},
        findings=tuple(findings),
    )
