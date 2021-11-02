# Licence Apache-2.0
from typing import List

import numpy as np

import feature_gen_dt

from ._base_datetime_feature import _BaseDatetimeFeature

from gators import DataFrame


class OrdinalMinuteOfHour(_BaseDatetimeFeature):
    """Create new columns based on the minute of the hour.

    Parameters
    ----------
    theta_vec : List[float]
        List of columns.

    Examples
    ---------
    Imports and initialization:

    >>> from gators.feature_generation_dt import OrdinalMinuteOfHour
    >>> obj = OrdinalMinuteOfHour(columns=['A'])

    The `fit`, `transform`, and `fit_transform` methods accept:

    * `dask` dataframes:

    >>> import dask.dataframe as dd
    >>> import pandas as pd
    >>> X = dd.from_pandas(pd.DataFrame(
    ... {'A': ['2020-01-01T23:00:00', '2020-12-15T18:59:00',  None], 'B': [0, 1, 0]}), npartitions=1)

    * `koalas` dataframes:

    >>> import databricks.koalas as ks
    >>> X = ks.DataFrame(
    ... {'A': ['2020-01-01T23:00:00', '2020-12-15T18:59:00',  None], 'B': [0, 1, 0]})


    * and `pandas` dataframes:

    >>> import pandas as pd
    >>> X = pd.DataFrame(
    ... {'A': ['2020-01-01T23:00:00', '2020-12-15T18:59:00',  None], 'B': [0, 1, 0]})


    The result is a transformed dataframe belonging to the same dataframe library.

    >>> obj.fit_transform(X)
                        A  B A__minute_of_hour
    0 2020-01-01 23:00:00  0               0.0
    1 2020-12-15 18:59:00  1              59.0
    2                 NaT  0               nan


    >>> X = pd.DataFrame(
    ... {'A': ['2020-01-01T23:00:00', '2020-12-15T18:59:00',  None], 'B': [0, 1, 0]})

    >>> _ = obj.fit(X)
    >>> obj.transform_numpy(X.to_numpy())
    array([[Timestamp('2020-01-01 23:00:00'), 0, '0.0'],
           [Timestamp('2020-12-15 18:59:00'), 1, '59.0'],
           [NaT, 0, 'nan']], dtype=object)
    """

    def __init__(self, columns: List[str], date_format: str = "ymd"):
        if not isinstance(columns, list):
            raise TypeError("`columns` should be a list.")
        if not columns:
            raise ValueError("`columns` should not be empty.")
        column_names = [f"{c}__minute_of_hour" for c in columns]
        _BaseDatetimeFeature.__init__(
            self, columns, date_format, column_names
        )

    def transform(self, X: DataFrame) -> DataFrame:
        """Transform the dataframe `X`.

        Parameters
        ----------
        X : DataFrame.
            Input dataframe.

        Returns
        -------
        X : DataFrame
            Transformed dataframe.
        """
        self.check_dataframe(X)

        for name, col in zip(self.column_names, self.columns):
            X[name] = X[col].dt.minute
        self.columns_ = list(X.columns)
        return X

    def transform_numpy(self, X: np.ndarray) -> np.ndarray:
        """Transform the array `X`.

        Parameters
        ----------
        X : np.ndarray
            Input array.

        Returns
        -------
        X : np.ndarray:
            Array with the datetime features added.
        """
        self.check_array(X)
        X_new = feature_gen_dt.ordinal_datetime(
            X[:, self.idx_columns], np.array([14, 16])
        )
        return np.concatenate([X, X_new], axis=1)
