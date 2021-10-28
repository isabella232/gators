# License: Apache-2.0
from typing import List, TypeVar

import databricks.koalas as ks
import numpy as np
import pandas as pd

from ..transformers.transformer import Transformer
from ..util import util

DataFrame = TypeVar("Union[pd.DataFrame, ks.DataFrame, dd.DataFrame]")
Series = TypeVar("Union[pd.DataFrame, ks.DataFrame, dd.DataFrame]")


class Pipeline(Transformer):
    """Chain the **gators** transformers together.

    Parameters
    ----------
    steps : List[Transformer]
        List of transformations.

    Examples
    ---------

    * fit & transform with `pandas`

    >>> import pandas as pd
    >>> import numpy as np
    >>> from gators.imputers import NumericsImputer
    >>> from gators.imputers import ObjectImputer
    >>> from gators.pipeline import Pipeline
    >>> X = pd.DataFrame({
    ...     'A': [0.1, 0.2, 0.3, np.nan],
    ...     'B': [1, 2, 2, np.nan],
    ...     'C': ['a', 'b', 'c', None]})
    >>> steps = [
    ...     ObjectImputer(strategy='constant', value='MISSING'),
    ...     NumericsImputer(strategy='median', columns=['A']),
    ...     NumericsImputer(strategy='most_frequent', columns=['B'])]
    >>> obj = Pipeline(steps=steps)
    >>> obj.fit_transform(X)
         A    B        C
    0  0.1  1.0        a
    1  0.2  2.0        b
    2  0.3  2.0        c
    3  0.2  2.0  MISSING

    * fit & transform with `koalas`

    >>> import databricks.koalas as ks
    >>> import numpy as np
    >>> from gators.imputers import NumericsImputer
    >>> from gators.imputers import ObjectImputer
    >>> from gators.pipeline import Pipeline
    >>> X = ks.DataFrame({
    ...     'A': [0.1, 0.2, 0.3, np.nan],
    ...     'B': [1, 2, 2, np.nan],
    ...     'C': ['a', 'b', 'c', None]})
    >>> steps = [
    ...     ObjectImputer(strategy='constant', value='MISSING'),
    ...     NumericsImputer(strategy='median', columns=['A']),
    ...     NumericsImputer(strategy='most_frequent', columns=['B'])]
    >>> obj = Pipeline(steps=steps)
    >>> obj.fit_transform(X)
         A    B        C
    0  0.1  1.0        a
    1  0.2  2.0        b
    2  0.3  2.0        c
    3  0.2  2.0  MISSING

    * fit with `pandas` & transform with `NumPy`

    >>> import pandas as pd
    >>> import numpy as np
    >>> from gators.imputers import NumericsImputer
    >>> from gators.imputers import ObjectImputer
    >>> from gators.pipeline import Pipeline
    >>> X = pd.DataFrame({
    ...     'A': [0.1, 0.2, 0.3, np.nan],
    ...     'B': [1, 2, 2, np.nan],
    ...     'C': ['a', 'b', 'c', None]})
    >>> steps = [
    ...     ObjectImputer(strategy='constant', value='MISSING'),
    ...     NumericsImputer(strategy='median', columns=['A']),
    ...     NumericsImputer(strategy='most_frequent', columns=['B'])]
    >>> obj = Pipeline(steps=steps)
    >>> _ = obj.fit(X)
    >>> obj.transform_numpy(X.to_numpy())
    array([[0.1, 1.0, 'a'],
           [0.2, 2.0, 'b'],
           [0.3, 2.0, 'c'],
           [0.2, 2.0, 'MISSING']], dtype=object)

    * fit with `koalas` & transform with `NumPy`

    >>> import databricks.koalas as ks
    >>> import numpy as np
    >>> from gators.imputers import NumericsImputer
    >>> from gators.imputers import ObjectImputer
    >>> from gators.pipeline import Pipeline
    >>> X = ks.DataFrame({
    ...     'A': [0.1, 0.2, 0.3, np.nan],
    ...     'B': [1, 2, 2, np.nan],
    ...     'C': ['a', 'b', 'c', None]})
    >>> steps = [
    ...     ObjectImputer(strategy='constant', value='MISSING'),
    ...     NumericsImputer(strategy='median', columns=['A']),
    ...     NumericsImputer(strategy='most_frequent', columns=['B'])]
    >>> obj = Pipeline(steps=steps)
    >>> _ = obj.fit(X)
    >>> obj.transform_numpy(X.to_numpy())
    array([[0.1, 1.0, 'a'],
           [0.2, 2.0, 'b'],
           [0.3, 2.0, 'c'],
           [0.2, 2.0, 'MISSING']], dtype=object)
    """

    def __init__(self, steps: List[Transformer]):
        if not isinstance(steps, list):
            raise TypeError("`steps` should be a list.")
        if not steps:
            raise TypeError("`steps` should be an empty list.")
        self.steps = steps
        self.is_model = (hasattr(self.steps[-1], "predict")) or (
            "pyspark.ml" in str(type(self.steps[-1]))
        )
        self.n_steps = len(self.steps)
        self.n_transformations = self.n_steps - 1 if self.is_model else self.n_steps
        self.problem_category = ""

    def fit(self, X: DataFrame, y: Series = None) -> "Pipeline":
        """Fit the transformer on the dataframe `X`.

        Parameters
        ----------
        X : DataFrame.
            Input dataframe.
        y : Series, default to None.
            Target values.

        Returns
        -------
        Pipeline
            Instance of itself.
        """
        self.base_columns = list(X.columns)
        for step in self.steps[: self.n_transformations]:
            step = step.fit(X, y)
            X = step.transform(X)
        if self.is_model:
            self.steps[-1] = util.get_function(X).fit(self.steps[-1], X, y)
        return self

    def transform(self, X: DataFrame) -> DataFrame:
        """Transform the dataframe `X`.

        Parameters
        ----------
        X : DataFrame.
            Input dataframe.

        Returns
        -------
        DataFrame
            Transformed dataframe.
        """
        self.check_dataframe(X)
        for step in self.steps[: self.n_transformations]:
            X = step.transform(X)
        return X

    def transform_numpy(self, X: np.ndarray) -> np.ndarray:
        """Transform the NumPy array `X`.

        Parameters
        ----------
        X : np.ndarray
            Input array.

        Returns
        -------
        np.ndarray
            Transformed array.
        """
        self.check_array(X)
        for step in self.steps[: self.n_transformations]:
            X = step.transform_numpy(X)
        return X

    def fit_transform(self, X: DataFrame, y: Series = None) -> DataFrame:
        """Fit and transform the pandas dataframe.

        Parameters
        ----------
        X : DataFrame
            Input dataframe.

        Returns
        -------
        DataFrame
            Transformed pandas dataframe.
        """
        self.base_columns = list(X.columns).copy()
        # self.problem_category = self.define_problem_category(y=y)
        for step in self.steps[: self.n_transformations]:
            step = step.fit(X, y)
            X = step.transform(X)
        return X

    def predict(self, X: DataFrame, y: Series = None) -> np.ndarray:
        """Predict on X, and predict.

        Parameters
        ----------
        X : DataFrame.
            Input dataframe.

        Returns
        -------
        np.ndarray
            Model predictions.
        """
        for step in self.steps[:-1]:
            X = step.transform(X)

        return util.get_function(X).predict(self.steps[-1], X)

    def predict_proba(self, X: DataFrame, y: np.array = None) -> np.ndarray:
        """Predict on X, and return the probability of success.

        Parameters
        ----------
        X : DataFrame.
            Input dataframe.

        Returns
        -------
        np.ndarray
            Model probabilities of success.
        """
        for step in self.steps[:-1]:
            X = step.transform(X)
        return util.get_function(X).predict_proba(self.steps[-1], X)

    def predict_numpy(self, X: np.ndarray, y: Series = None) -> np.ndarray:
        """Predict on X, and predict.

        Parameters
        ----------
        X : DataFrame.
            Input dataframe.

        Returns
        -------
        np.ndarray
            Model predictions.
        """
        for step in self.steps[:-1]:
            X = step.transform_numpy(X)
        return self.steps[-1].predict(X)

    def predict_proba_numpy(self, X: np.ndarray) -> np.ndarray:
        """Predict on X, and return the probability of success.

        Parameters
        ----------
        X  : np.ndarray
            Input array.

        Returns
        -------
        np.ndarray
            Model probabilities of success.
        """
        for step in self.steps[:-1]:
            X = step.transform_numpy(X)
        return self.steps[-1].predict_proba(X)

    def get_feature_importances(self, k: int) -> pd.Series:
        """Get the feature importances of the pipeline.

        Parameters
        ----------
        k int
            Number of top features to return.

        Returns
        -------
        pd.Series
            Feature importances.
        """
        if not hasattr(self.steps[-1], "feature_importances_"):
            raise AttributeError(
                """The last step of the pipeline should have
                 the attribute `feature_importances_`"""
            )
        feature_importances_ = self.steps[-1].feature_importances_
        return feature_importances_.sort_values(ascending=False).iloc[:k]

    def get_features(self) -> List[str]:
        """Get the feature importances of the pipeline.

        Parameters
        ----------
        k int
            Number of top features to return.

        Returns
        -------
        List[str]
            List of features.
        """
        if not hasattr(self.steps[-1], "selected_columns"):
            raise AttributeError(
                """The last step of the pipeline should have
                 the attribute `selected_columns`"""
            )
        return self.steps[-1].selected_columns

    def get_production_columns(self):
        has_feature_importances_ = hasattr(self.steps[-1], "feature_importances_")
        if not has_feature_importances_:
            raise AttributeError(
                """The last step of the pipeline should contains
                the atrribute `feature_importances_`"""
            )
        features = self.steps[-1].selected_columns

        base_columns_ = features.copy()
        for step in self.steps[::-1]:
            if not hasattr(step, "column_names"):
                continue
            for i, col in enumerate(base_columns_):
                if col in step.column_mapping:
                    base_columns_[i] = step.column_mapping[col]
            base_columns_ = list(set(util.flatten_list(base_columns_)))
        base_columns_ = list(set(base_columns_))
        prod_columns = [c for c in self.base_columns if c in base_columns_]
        return prod_columns
