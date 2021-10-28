# License: Apache-2.0
import databricks.koalas as ks
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from gators.feature_generation_dt import OrdinalHourOfDay

ks.set_option("compute.default_index_type", "distributed-sequence")


@pytest.fixture
def data_ks():
    X = ks.DataFrame(
        {
            "A": ["2020-05-04 00:00:00", pd.NaT],
            "B": ["2020-05-06 06:00:00", pd.NaT],
            "C": ["2020-05-08 12:00:00", pd.NaT],
            "D": ["2020-05-09 18:00:00", pd.NaT],
            "E": ["2020-05-10 23:00:00", pd.NaT],
            "X": ["x", "x"],
        }
    )
    columns = ["A", "B", "C", "D", "E"]
    X[columns] = X[columns].astype("datetime64[ns]")

    X_expected = pd.DataFrame(
        {
            "A__hour_of_day": ["0.0", "nan"],
            "B__hour_of_day": ["6.0", "nan"],
            "C__hour_of_day": ["12.0", "nan"],
            "D__hour_of_day": ["18.0", "nan"],
            "E__hour_of_day": ["23.0", "nan"],
        }
    )
    X_expected = pd.concat([X.to_pandas().copy(), X_expected], axis=1)
    obj = OrdinalHourOfDay(columns=columns).fit(X)
    return obj, X, X_expected


@pytest.mark.koalas
def test_ks(data_ks):
    obj, X, X_expected = data_ks
    X_new = obj.transform(X)
    assert_frame_equal(X_new.to_pandas(), X_expected)


@pytest.mark.koalas
def test_ks_np(data_ks):
    obj, X, X_expected = data_ks
    X_numpy_new = obj.transform_numpy(X.to_numpy())
    X_new = pd.DataFrame(X_numpy_new)
    X_expected = pd.DataFrame(X_expected.values)
    assert_frame_equal(X_new, X_expected)
