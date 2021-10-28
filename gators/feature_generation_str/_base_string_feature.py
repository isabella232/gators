# Licence Apache-2.0

from typing import List, TypeVar

import numpy as np

from ..transformers.transformer import Transformer
from ..util import util

DataFrame = TypeVar("Union[pd.DataFrame, ks.DataFrame, dd.DataFrame]")
Series = TypeVar("Union[pd.DataFrame, ks.DataFrame, dd.DataFrame]")


class _BaseStringFeature(Transformer):
    """Base string feature transformer class.

    Parameters
    ----------
    columns : List[str]
        List of columns.
    column_names : List[str], default to None.
        List of column names.

    """

    def __init__(self, columns: List[str], column_names: List[str]):
        if not isinstance(columns, list):
            raise TypeError("`columns` should be a list.")
        if not columns:
            raise ValueError("`columns` should not be empty.")
        if column_names and not isinstance(column_names, list):
            raise TypeError("`column_names` should be a list.")
        if column_names and len(column_names) != len(columns):
            raise ValueError("Length of `columns` and `column_names` should match.")
        Transformer.__init__(self)
        self.columns = columns
        self.column_names: List[str] = column_names
        self.column_mapping = dict(zip(column_names, columns))
        self.idx_columns: np.ndarray = np.array([])

    def fit(self, X: DataFrame, y: Series = None) -> "_BaseStringFeature":
        """Fit the transformer on the dataframe `X`.

        Parameters
        ----------
        X : pd.DataFrame
            Input dataframe.
        y : Series, default to None.
            Target values.

        Returns
        -------
        _BaseStringFeature
            Instance of itself.
        """
        self.check_dataframe(X)
        self.idx_columns = util.get_idx_columns(
            columns=X.columns,
            selected_columns=self.columns,
        )
        return self
