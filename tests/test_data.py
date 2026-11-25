"""Checks on the data file and the pre-registered answer key (spec §3)."""
import numpy as np
import pytest

from answerkey.toolkit import (
    TRUTH_PP_EXPECTED,
    TRUTH_SE_PP_EXPECTED,
    complete_cases,
    difference_in_means_pp,
    load_data,
)


@pytest.fixture(scope="module")
def df():
    return load_data()


def test_row_counts(df):
    assert len(df) == 50_083
    assert int(df.treatment.sum()) == 33_396
    assert len(complete_cases(df)) == 48_899


def test_factor_codes(df):
    treated = df[df.treatment == 1]
    assert sorted(treated.ratio.unique()) == [1, 2, 3]
    assert sorted(treated["size"].unique()) == [1, 2, 3, 4]
    assert sorted(treated.ask.unique()) == [1, 2, 3]
    assert set(df[df.treatment == 0][["ratio", "size", "ask"]].stack().unique()) == {0}


def test_dormant_is_recency_threshold(df):
    has_mrm2 = df.mrm2.notna()
    assert has_mrm2.sum() == 50_082
    assert np.array_equal(df.loc[has_mrm2, "dormant"], (df.loc[has_mrm2, "mrm2"] >= 8).astype(int))


def test_answer_key(df):
    cc = complete_cases(df)
    truth, se = difference_in_means_pp(cc.gave, cc.treatment)
    assert abs(truth - TRUTH_PP_EXPECTED) < 5e-5
    assert abs(se - TRUTH_SE_PP_EXPECTED) < 5e-5
