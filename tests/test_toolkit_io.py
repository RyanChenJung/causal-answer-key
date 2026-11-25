"""Checks on the shared toolkit's I/O helpers (spec §12.5, §12.8)."""
import pytest

from answerkey import toolkit


def test_truth_constants():
    assert abs(toolkit.TRUTH_PP - 0.4479) < 5e-5
    assert abs(toolkit.TRUTH_SE_PP - 0.1318) < 5e-5


def test_dev_results_go_under_results_dev():
    assert toolkit.results_path("x.csv", dev=True).parent.name == "dev"
    assert toolkit.results_path("x.csv", dev=False).parent == toolkit.RESULTS_DIR


def test_record_key_rejects_bad_units_and_names():
    with pytest.raises(ValueError):
        toolkit.record_key("truth_ate_pp", 0.45, "percent", "test")
    with pytest.raises(ValueError):
        toolkit.record_key("Truth ATE", 0.45, "pp", "test")


def test_save_figure_rejects_unknown_names():
    with pytest.raises(ValueError):
        toolkit.save_figure(None, "fig99_unknown")


def test_production_child_index():
    assert toolkit.production_child("A", 0) == 0
    assert toolkit.production_child("C", 49) == 149
