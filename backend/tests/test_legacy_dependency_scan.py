from pathlib import Path

from bgpkb.ingestion.legacy_dependency_scan import scan_v1_dependencies


def test_dependency_scan_blocks_v1_reads_in_new_production_code(tmp_path):
    source = tmp_path / "src" / "bgpkb" / "semantic"
    source.mkdir(parents=True)
    (source / "builder.py").write_text(
        "from bgpkb import paths\nROOT = paths.CHUNKS_DIR\n",
        encoding="utf-8",
    )

    report = scan_v1_dependencies(tmp_path)

    assert report["summary"] == {"references": 1, "blocking": 1, "deprecated": 0}
    assert report["blocking_references"][0]["symbol"] == "CHUNKS_DIR"


def test_dependency_scan_classifies_explicit_adapter_as_deprecated_not_production(tmp_path):
    migration = tmp_path / "src" / "bgpkb" / "ingestion"
    migration.mkdir(parents=True)
    (migration / "legacy_migration.py").write_text(
        "from bgpkb.ingestion.legacy_canonical_adapter import read_legacy_read_only\n"
        "payload = read_legacy_read_only(path, allow_legacy=True)\n",
        encoding="utf-8",
    )

    report = scan_v1_dependencies(tmp_path)

    assert report["summary"] == {"references": 1, "blocking": 0, "deprecated": 1}
    assert report["deprecated_references"][0]["symbol"] == "read_legacy_read_only"


def test_dependency_scan_is_stable_and_ignores_tests_and_generated_reports(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_old.py").write_text("value = 'data/corpus/chunks/'\n", encoding="utf-8")
    report_dir = tmp_path / "data" / "generated" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "old.md").write_text("data/corpus/parsed/\n", encoding="utf-8")

    first = scan_v1_dependencies(tmp_path)
    second = scan_v1_dependencies(tmp_path)

    assert first == second
    assert first["summary"]["references"] == 0


def test_dependency_scan_does_not_double_count_compatibility_symlinks(tmp_path):
    implementation = tmp_path / "src" / "bgpkb" / "ingestion" / "old.py"
    implementation.parent.mkdir(parents=True)
    implementation.write_text("from bgpkb import paths\nROOT = paths.PARSED_DIR\n", encoding="utf-8")
    compatibility = tmp_path / "src" / "bgpkb" / "pipeline" / "old.py"
    compatibility.parent.mkdir(parents=True)
    compatibility.symlink_to(Path("../ingestion/old.py"))

    report = scan_v1_dependencies(tmp_path)

    assert report["summary"]["references"] == 1


def test_repository_policy_has_no_unclassified_v1_production_dependency():
    repository_root = Path(__file__).resolve().parents[2]

    report = scan_v1_dependencies(repository_root)

    assert report["summary"]["blocking"] == 0
    assert all("retrieval/run_" not in row["path"] for row in report["deprecated_references"])
