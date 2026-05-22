import json
import subprocess
from pathlib import Path

from tests.cypher_tck import coverage_gap_report


def _write_py(path: Path, line_count: int = 4) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"x_{index} = {index}" for index in range(line_count)) + "\n")


def _pygraphistry_root(tmp_path: Path) -> Path:
    root = tmp_path / "pygraphistry"
    for relative in coverage_gap_report.PRIORITY_FILES:
        _write_py(root / relative)
    _write_py(root / "graphistry/compute/gfql/extra.py")
    _write_py(root / "graphistry/compute/predicates/filter.py")
    _write_py(root / "graphistry/compute/ast.py")
    _write_py(root / "graphistry/compute/chain.py")
    _write_py(root / "graphistry/compute/hop.py")
    return root


def test_discover_target_files_prioritizes_requested_files(tmp_path) -> None:
    root = _pygraphistry_root(tmp_path)

    discovered = [
        path.relative_to(root).as_posix()
        for path in coverage_gap_report.discover_target_files(root)
    ]

    assert discovered[: len(coverage_gap_report.PRIORITY_FILES)] == list(
        coverage_gap_report.PRIORITY_FILES
    )
    assert "graphistry/compute/gfql/extra.py" in discovered
    assert "graphistry/compute/predicates/filter.py" in discovered
    assert "graphistry/compute/ast.py" in discovered


def test_build_report_groups_zero_hit_ranges_and_renders_markdown(tmp_path) -> None:
    root = _pygraphistry_root(tmp_path)
    file_path = root / "graphistry/compute/gfql/cypher/lowering.py"
    file_coverage = coverage_gap_report.FileCoverage(
        path=file_path,
        relative_path="graphistry/compute/gfql/cypher/lowering.py",
        total_lines=10,
        executable_lines=(1, 2, 3, 5, 6, 9),
        missing_lines=(2, 3, 6, 9),
        hit_lines=(1, 5),
    )

    report = coverage_gap_report.build_report(
        files=[file_coverage],
        checkout_dir=tmp_path,
        pygraphistry_root=root,
        coverage_data=tmp_path / ".coverage",
        runner=coverage_gap_report.RunnerResult(returncode=0, command=("pytest",)),
        generated_at="2026-05-21T00:00:00Z",
    )
    markdown = coverage_gap_report.render_markdown(report)

    assert report["schema_version"] == 1
    assert report["summary_counts"]["zero_hit_line_count"] == 4
    assert report["priority_files"][0]["zero_hit_ranges"] == [
        {"start": 2, "end": 3},
        {"start": 6, "end": 6},
        {"start": 9, "end": 9},
    ]
    assert "Coverage Gap Report" in markdown
    assert "`graphistry/compute/gfql/cypher/lowering.py`" in markdown
    assert "2-3, 6, 9" in markdown
    assert "coverage evidence only" in markdown


def test_run_scenarios_under_coverage_creates_data_parent_and_restricts_include(
    tmp_path, monkeypatch
) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    target_file = tmp_path / "pygraphistry/graphistry/compute/gfql_unified.py"
    _write_py(target_file)
    coverage_data = tmp_path / "nested" / "coverage" / ".coverage"
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(coverage_gap_report.subprocess, "run", fake_run)

    result = coverage_gap_report.run_scenarios_under_coverage(
        checkout_dir=checkout,
        pygraphistry_path=tmp_path / "pygraphistry",
        coverage_data=coverage_data,
        target_files=[target_file],
        pytest_args=["tests/cypher_tck/test_tck_runner.py", "-q"],
    )

    command, kwargs = calls[0]
    assert coverage_data.parent.is_dir()
    assert result.returncode == 0
    assert "--include" in command
    assert str(target_file.resolve()) in command
    assert kwargs["cwd"] == checkout
    assert str(tmp_path / "pygraphistry") in kwargs["env"]["PYTHONPATH"]


def test_main_writes_json_and_markdown_with_mocked_coverage_run(tmp_path, monkeypatch) -> None:
    root = _pygraphistry_root(tmp_path)
    json_output = tmp_path / "coverage-gap.json"
    markdown_output = tmp_path / "coverage-gap.md"
    coverage_data = tmp_path / ".coverage"

    def fake_run(**kwargs):
        assert kwargs["pytest_args"] == ("tests/cypher_tck/test_tck_runner.py", "-q")
        return coverage_gap_report.RunnerResult(returncode=0, command=("coverage", "run"))

    def fake_analyze(**kwargs):
        target = root / "graphistry/compute/gfql/row/pipeline.py"
        return [
            coverage_gap_report.FileCoverage(
                path=target,
                relative_path="graphistry/compute/gfql/row/pipeline.py",
                total_lines=4,
                executable_lines=(1, 2, 3, 4),
                missing_lines=(3, 4),
                hit_lines=(1, 2),
            )
        ]

    monkeypatch.setattr(coverage_gap_report, "run_scenarios_under_coverage", fake_run)
    monkeypatch.setattr(coverage_gap_report, "analyze_coverage_data", fake_analyze)

    coverage_gap_report.main(
        [
            "--checkout-dir",
            str(tmp_path),
            "--pygraphistry-path",
            str(root),
            "--coverage-data",
            str(coverage_data),
            "--json-output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
        ]
    )

    parsed = json.loads(json_output.read_text(encoding="utf-8"))
    markdown = markdown_output.read_text(encoding="utf-8")

    assert parsed["schema_version"] == 1
    assert parsed["runner"]["returncode"] == 0
    assert parsed["priority_files"][0]["path"] == "graphistry/compute/gfql/row/pipeline.py"
    assert "# Coverage Gap Report" in markdown
