from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

from tests.cypher_tck import report
from tests.cypher_tck.comparator import compare_expected_error
from tests.cypher_tck.direct_cypher_xfail_contract import (
    DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY,
)
from tests.cypher_tck.gap_priority import classify_primary_xfail_family
from tests.cypher_tck.models import Scenario
from tests.cypher_tck.scenarios import SCENARIOS

MANIFEST_SCHEMA_VERSION = 2
DEFAULT_MANIFEST_PATH = Path("tests/cypher_tck/capability_debt_manifest.json")
ALLOWED_SUPPORT_STATUSES = frozenset({"supported", "xfail", "skip", "other"})
ALLOWED_IMPLEMENTATION_STATUSES = frozenset(
    {"translated", "direct_cypher_only", "not_yet_implemented"}
)
EXPECTED_ERROR_CASE_CATEGORY = "expected_error"
CATEGORY_DEFINITIONS = {
    "supported": "Current expected-pass scenario, including translated GFQL and direct-Cypher-only promotions.",
    "xfail": "Known conformance debt that remains represented in the harness with a reason string.",
    "skip": "Temporarily excluded scenario status; no scenarios currently use this status.",
    "not_yet_implemented": "Scenario without translated GFQL and without direct-Cypher-only promotion.",
}

# Capability/debt manifest contract:
# - `schema_version` starts at 1 and is bumped for shape or meaning changes
#   that downstream consumers should explicitly acknowledge.
# - The manifest is scenario-level metadata. It does not copy the #147 report
#   artifact source refs, runtime profile, or headline-count ownership.
# - Validation consumes the #147 JSON artifact so future snapshot-delta and
#   conformance handoff tools can reconcile against one stable report contract.


class ManifestValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


@dataclass(frozen=True)
class ManifestValidationSummary:
    scenario_count: int
    status_counts: dict[str, int]
    implementation_counts: dict[str, int]
    direct_cypher_debt_count: int

    def format(self) -> str:
        return (
            "capability/debt manifest valid: "
            f"{self.scenario_count} scenario entries; "
            f"status_counts={self.status_counts}; "
            f"implementation_counts={self.implementation_counts}; "
            f"direct_cypher_debt_count={self.direct_cypher_debt_count}"
        )


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_report_artifact(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _implementation_status(scenario: Scenario) -> str:
    if scenario.gfql is not None:
        return "translated"
    if "cypher-string" in scenario.tags:
        return "direct_cypher_only"
    return "not_yet_implemented"


def _ownership_label(scenario: Scenario) -> str:
    if scenario.status == "xfail":
        return classify_primary_xfail_family(scenario)
    if scenario.status == "skip":
        return "skipped"
    if _implementation_status(scenario) == "direct_cypher_only":
        return "direct-cypher-promotion"
    return "supported"


def _direct_cypher_debt_entry(key: str) -> dict[str, str] | None:
    outcome = DIRECT_CYPHER_NONVALIDATION_XFAIL_OUTCOME_BY_KEY.get(key)
    if outcome is None:
        return None
    return {
        "outcome": outcome,
        "reason": f"direct_cypher_nonvalidation:{outcome}",
    }


def build_manifest(scenarios: Sequence[Scenario] = SCENARIOS) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for scenario in sorted(scenarios, key=lambda item: item.key):
        entry: dict[str, Any] = {
            "key": scenario.key,
            "support_status": (
                scenario.status
                if scenario.status in ALLOWED_SUPPORT_STATUSES
                else "other"
            ),
            "implementation_status": _implementation_status(scenario),
            "ownership": _ownership_label(scenario),
            "tags": sorted(scenario.tags),
        }
        if scenario.reason:
            entry["reason"] = scenario.reason
        direct_cypher_debt = _direct_cypher_debt_entry(scenario.key)
        if direct_cypher_debt is not None:
            entry["direct_cypher_debt"] = direct_cypher_debt
        entries.append(entry)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "compatible_report_schema_version": report.SCHEMA_VERSION,
        "category_definitions": CATEGORY_DEFINITIONS,
        "scenario_entries": entries,
    }


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _artifact_debt_by_key(artifact: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    debt_entries = artifact.get("debt_keys", [])
    if not isinstance(debt_entries, list):
        return {}
    debt_by_key: dict[str, dict[str, str]] = {}
    for item in debt_entries:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        outcome = item.get("outcome")
        reason = item.get("reason")
        if (
            isinstance(key, str)
            and isinstance(outcome, str)
            and isinstance(reason, str)
        ):
            debt_by_key[key] = {"outcome": outcome, "reason": reason}
    return debt_by_key


def _normalize_case_category(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized in {
        "error",
        "errors",
        "expected_error",
        "expected_errors",
        "expectederror",
    }:
        return EXPECTED_ERROR_CASE_CATEGORY
    return normalized or None


def _artifact_expected_error_by_key(
    artifact: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    cases = artifact.get("direct_cypher_cases")
    if not isinstance(cases, list):
        return {}

    errors_by_key: dict[str, Mapping[str, Any]] = {}
    for item in cases:
        if not isinstance(item, Mapping):
            continue
        key = item.get("key")
        if not isinstance(key, str) or not key:
            continue
        category = _normalize_case_category(item.get("category", item.get("status")))
        if category != EXPECTED_ERROR_CASE_CATEGORY:
            continue
        errors_by_key[key] = _normalize_actual_expected_error(item)
    return errors_by_key


def _normalize_actual_expected_error(case: Mapping[str, Any]) -> Mapping[str, Any]:
    nested = case.get("expected_error")
    if isinstance(nested, Mapping):
        payload: dict[str, Any] = dict(nested)
    else:
        payload = {}

    for source, target in (
        ("code", "code"),
        ("error_code", "code"),
        ("category", "case_category"),
        ("error_category", "category"),
        ("field", "field"),
        ("value", "value"),
        ("message", "message"),
        ("error_message", "message"),
        ("detail", "message"),
    ):
        if target not in payload and source in case:
            payload[target] = case[source]
    return payload


def _manifest_expected_error(
    value: object,
    *,
    key: str,
    errors: list[str],
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        errors.append(f"{key}.expected_error must be an object")
        return None

    code = value.get("code")
    if not isinstance(code, str) or not code.strip():
        errors.append(f"{key}.expected_error.code must be a non-empty string")
        return None

    payload: dict[str, Any] = {"code": code}
    key_fields = value.get("key_fields", {})
    if not isinstance(key_fields, Mapping):
        errors.append(f"{key}.expected_error.key_fields must be an object when present")
        key_fields = {}
    for field, field_value in key_fields.items():
        if not isinstance(field, str) or not field.strip():
            errors.append(f"{key}.expected_error.key_fields keys must be strings")
            continue
        payload[field] = field_value

    anchored_substrings = value.get("anchored_substrings", [])
    if not isinstance(anchored_substrings, list) or not all(
        isinstance(item, str) and item for item in anchored_substrings
    ):
        errors.append(
            f"{key}.expected_error.anchored_substrings must be a list of "
            "non-empty strings when present"
        )
        anchored_substrings = []
    payload["anchored_substrings"] = tuple(cast(list[str], anchored_substrings))
    payload["key_field_names"] = tuple(
        field for field in key_fields if isinstance(field, str) and field.strip()
    )
    return payload


def _error_message(actual_error: Mapping[str, Any]) -> str:
    message = actual_error.get("message")
    if message is None:
        return ""
    return str(message)


def _expected_error_claim_diagnostic(
    *,
    key: str,
    expected_error: Mapping[str, Any],
    actual_error: Mapping[str, Any] | None,
) -> str:
    actual_payload = actual_error or {"code": "<missing error code>"}
    result = compare_expected_error(
        scenario_key=key,
        expected=expected_error,
        actual=actual_payload,
        key_fields=cast(Sequence[str], expected_error.get("key_field_names", ())),
    )
    if result.matched:
        return ""
    return f"{key}: expected_error claim mismatch\n{result.diagnostic}"


def _expected_error_drift_diagnostic(
    *,
    key: str,
    expected_error: Mapping[str, Any],
    actual_error: Mapping[str, Any],
) -> str:
    result = compare_expected_error(
        scenario_key=key,
        expected=expected_error,
        actual=actual_error,
        key_fields=cast(Sequence[str], expected_error.get("key_field_names", ())),
    )
    if result.matched:
        for index, substring in enumerate(
            cast(Sequence[str], expected_error.get("anchored_substrings", ()))
        ):
            message = _error_message(actual_error)
            if substring not in message:
                return (
                    f"{key}: expected_error drift\n"
                    f"expected error mismatch for scenario {key}\n"
                    f"context: field='anchored_substrings[{index}]'\n"
                    f"expected: {substring!r}\n"
                    f"actual: {message!r}\n"
                    "note: anchored substring was not present in actual error text"
                )
        return ""
    return f"{key}: expected_error drift\n{result.diagnostic}"


def _current_status_counts(scenarios: Sequence[Scenario]) -> dict[str, int]:
    counter = Counter(scenario.status for scenario in scenarios)
    return {
        "total": len(scenarios),
        "supported": counter.get("supported", 0),
        "xfail": counter.get("xfail", 0),
        "skip": counter.get("skip", 0),
        "other": len(scenarios)
        - counter.get("supported", 0)
        - counter.get("xfail", 0)
        - counter.get("skip", 0),
    }


def _require_mapping(value: object, name: str, errors: list[str]) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    errors.append(f"{name} must be an object")
    return {}


def _require_entries(value: object, errors: list[str]) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        errors.append("scenario_entries must be a list")
        return []
    entries: list[Mapping[str, Any]] = []
    for idx, entry in enumerate(value):
        if isinstance(entry, Mapping):
            entries.append(entry)
        else:
            errors.append(f"scenario_entries[{idx}] must be an object")
    return entries


def validate_manifest(
    manifest: Mapping[str, Any],
    *,
    artifact: Mapping[str, Any],
    scenarios: Sequence[Scenario] = SCENARIOS,
) -> ManifestValidationSummary:
    errors: list[str] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append(
            "manifest schema_version must be "
            f"{MANIFEST_SCHEMA_VERSION}, got {manifest.get('schema_version')!r}"
        )
    if manifest.get("compatible_report_schema_version") != report.SCHEMA_VERSION:
        errors.append(
            "manifest compatible_report_schema_version must be "
            f"{report.SCHEMA_VERSION}, got "
            f"{manifest.get('compatible_report_schema_version')!r}"
        )
    if artifact.get("schema_version") != manifest.get(
        "compatible_report_schema_version"
    ):
        errors.append(
            "report artifact schema_version does not match manifest "
            "compatible_report_schema_version"
        )
    category_definitions = _require_mapping(
        manifest.get("category_definitions"), "category_definitions", errors
    )
    for category in CATEGORY_DEFINITIONS:
        definition = category_definitions.get(category)
        if not isinstance(definition, str) or not definition.strip():
            errors.append(f"category_definitions.{category} must be documented")

    entries = _require_entries(manifest.get("scenario_entries"), errors)
    scenarios_by_key = {scenario.key: scenario for scenario in scenarios}
    current_keys = sorted(scenarios_by_key)
    manifest_keys = [entry.get("key") for entry in entries]
    string_manifest_keys = [key for key in manifest_keys if isinstance(key, str)]

    if len(string_manifest_keys) != len(set(string_manifest_keys)):
        duplicates = sorted(
            key for key, count in Counter(string_manifest_keys).items() if count > 1
        )
        errors.append(f"duplicate manifest scenario keys: {duplicates[:10]}")
    if string_manifest_keys != sorted(string_manifest_keys):
        errors.append("manifest scenario_entries must be sorted by key")

    unknown_keys = sorted(set(string_manifest_keys) - set(current_keys))
    missing_keys = sorted(set(current_keys) - set(string_manifest_keys))
    if unknown_keys:
        errors.append(f"unknown scenario keys in manifest: {unknown_keys[:10]}")
    if missing_keys:
        errors.append(
            f"missing manifest entries for current scenarios: {missing_keys[:10]}"
        )

    status_counts: Counter[str] = Counter()
    implementation_counts: Counter[str] = Counter()
    manifest_debt_by_key: dict[str, dict[str, str]] = {}
    actual_expected_error_by_key = _artifact_expected_error_by_key(artifact)
    manifest_expected_error_by_key: dict[str, Mapping[str, Any]] = {}

    for idx, entry in enumerate(entries):
        key = entry.get("key")
        if not isinstance(key, str):
            errors.append(f"scenario_entries[{idx}].key must be a string")
            continue
        scenario = scenarios_by_key.get(key)
        support_status = entry.get("support_status")
        implementation_status = entry.get("implementation_status")
        reason = entry.get("reason")
        ownership = entry.get("ownership")
        tags = entry.get("tags")
        expected_error = _manifest_expected_error(
            entry.get("expected_error"),
            key=key,
            errors=errors,
        )
        if expected_error is not None:
            manifest_expected_error_by_key[key] = expected_error

        if support_status not in ALLOWED_SUPPORT_STATUSES:
            errors.append(f"{key}: unsupported support_status {support_status!r}")
        if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            errors.append(
                f"{key}: unsupported implementation_status {implementation_status!r}"
            )
        if not isinstance(ownership, str) or not ownership.strip():
            errors.append(f"{key}: ownership must be a non-empty string")
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            errors.append(f"{key}: tags must be a list of strings")

        if scenario is None:
            continue

        expected_support_status = (
            scenario.status if scenario.status in ALLOWED_SUPPORT_STATUSES else "other"
        )
        expected_implementation_status = _implementation_status(scenario)
        expected_reason = scenario.reason
        expected_tags = sorted(scenario.tags)
        expected_ownership = _ownership_label(scenario)

        if support_status != expected_support_status:
            errors.append(
                f"{key}: support_status {support_status!r} does not match "
                f"scenario status {expected_support_status!r}"
            )
        if implementation_status != expected_implementation_status:
            errors.append(
                f"{key}: implementation_status {implementation_status!r} does not "
                f"match current {expected_implementation_status!r}"
            )
        if support_status in {"xfail", "skip"} or (
            implementation_status == "not_yet_implemented"
        ):
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{key}: missing reason for debt/status entry")
        if expected_reason is None:
            if "reason" in entry and reason not in (None, ""):
                errors.append(f"{key}: manifest reason should be absent")
        elif reason != expected_reason:
            errors.append(f"{key}: reason does not match current Scenario.reason")
        if tags != expected_tags:
            errors.append(f"{key}: tags do not match current scenario tags")
        if ownership != expected_ownership:
            errors.append(f"{key}: ownership does not match current ownership label")

        direct_cypher_debt = entry.get("direct_cypher_debt")
        if direct_cypher_debt is not None:
            debt_mapping = _require_mapping(
                direct_cypher_debt, f"{key}.direct_cypher_debt", errors
            )
            outcome = debt_mapping.get("outcome")
            debt_reason = debt_mapping.get("reason")
            if isinstance(outcome, str) and isinstance(debt_reason, str):
                manifest_debt_by_key[key] = {
                    "outcome": outcome,
                    "reason": debt_reason,
                }

        if isinstance(support_status, str):
            status_counts.update([support_status])
        if isinstance(implementation_status, str):
            implementation_counts.update([implementation_status])

    for key, expected_error in sorted(manifest_expected_error_by_key.items()):
        actual_error = actual_expected_error_by_key.get(key)
        if actual_error is None:
            errors.append(
                _expected_error_claim_diagnostic(
                    key=key,
                    expected_error=expected_error,
                    actual_error=None,
                )
            )
            continue
        diagnostic = _expected_error_drift_diagnostic(
            key=key,
            expected_error=expected_error,
            actual_error=actual_error,
        )
        if diagnostic:
            errors.append(diagnostic)

    for key, actual_error in sorted(actual_expected_error_by_key.items()):
        if key in manifest_expected_error_by_key:
            continue
        if actual_error.get("code") is not None:
            errors.append(
                f"{key}: expected_error drift\n"
                "actual direct_cypher_cases entry has structured expected-error "
                "output, but manifest expected_error block is absent"
            )

    source_refs = _require_mapping(artifact.get("source_refs"), "source_refs", errors)
    local_fixtures = _require_mapping(
        source_refs.get("local_fixtures"),
        "source_refs.local_fixtures",
        errors,
    )
    expected_inventory_hash = report._scenario_inventory_revision(scenarios)
    if local_fixtures.get("scenario_inventory_sha256") != expected_inventory_hash:
        errors.append("report artifact scenario inventory hash is stale")

    scenario_counts = _require_mapping(
        artifact.get("scenario_counts"),
        "scenario_counts",
        errors,
    )
    expected_status_counts = _current_status_counts(scenarios)
    for field, expected in expected_status_counts.items():
        if scenario_counts.get(field) != expected:
            errors.append(
                f"report artifact scenario_counts.{field}="
                f"{scenario_counts.get(field)!r} does not match current {expected}"
            )
    for field in ("supported", "xfail", "skip", "other"):
        if status_counts.get(field, 0) != expected_status_counts[field]:
            errors.append(
                f"manifest support_status count for {field}="
                f"{status_counts.get(field, 0)} does not match current "
                f"{expected_status_counts[field]}"
            )

    expected_debt_by_key = _artifact_debt_by_key(artifact)
    if manifest_debt_by_key != expected_debt_by_key:
        errors.append(
            "manifest direct_cypher_debt entries do not match report debt_keys"
        )

    expected_error_counts = _require_mapping(
        artifact.get("expected_error_counts"),
        "expected_error_counts",
        errors,
    )
    if expected_error_counts.get("direct_cypher_nonvalidation_debt") != len(
        expected_debt_by_key
    ):
        errors.append(
            "report expected_error_counts.direct_cypher_nonvalidation_debt "
            "does not match report debt_keys"
        )

    if errors:
        raise ManifestValidationError(errors)

    return ManifestValidationSummary(
        scenario_count=len(entries),
        status_counts=dict(sorted(status_counts.items())),
        implementation_counts=dict(sorted(implementation_counts.items())),
        direct_cypher_debt_count=len(manifest_debt_by_key),
    )


def validate_default_manifest(
    *,
    artifact: Mapping[str, Any] | None = None,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> ManifestValidationSummary:
    return validate_manifest(
        load_manifest(manifest_path),
        artifact=artifact
        or report.build_json_artifact(generated_at="1970-01-01T00:00:00Z"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the tck-gfql capability/debt manifest."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=f"Manifest path (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=report.DEFAULT_JSON_OUTPUT,
        help=f"#147 report artifact path (default: {report.DEFAULT_JSON_OUTPUT})",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write the current generated manifest to this path and exit.",
    )
    args = parser.parse_args()

    if args.write is not None:
        write_manifest(args.write, build_manifest())
        print(f"Capability/debt manifest written: {args.write}")
        return

    artifact = load_report_artifact(args.report_json)
    summary = validate_manifest(load_manifest(args.manifest), artifact=artifact)
    print(summary.format())


if __name__ == "__main__":
    main()
