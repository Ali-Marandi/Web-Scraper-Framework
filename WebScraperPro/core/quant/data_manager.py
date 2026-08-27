r"""
Quantitative Finance - Data Manager
Handles data ingestion from scraped results, CSV/Excel files, and programmatic input.
Converts raw data into standardized time-series formats for all quant modules.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union, Tuple
from dataclasses import dataclass, field
import warnings

warnings.filterwarnings("ignore")


@dataclass
class TimeSeriesData:
    """Standardized time-series container for quant analysis."""
    name: str
    df: pd.DataFrame
    value_column: str = "close"
    date_column: str = "date"
    frequency: str = "daily"  # daily, hourly, weekly, monthly
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def values(self) -> np.ndarray:
        col = self.value_column
        if col in self.df.columns:
            return self.df[col].values.astype(float)
        # Try to find a numeric column
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            return self.df[numeric_cols[0]].values.astype(float)
        raise ValueError(f"No numeric column found in data for '{self.name}'")

    @property
    def dates(self) -> np.ndarray:
        if self.date_column in self.df.columns:
            return pd.to_datetime(self.df[self.date_column]).values
        return np.arange(len(self.df))

    @property
    def returns(self) -> np.ndarray:
        vals = self.values
        return np.diff(np.log(vals + 1e-10))

    @property
    def n_observations(self) -> int:
        return len(self.df)

    def summary(self) -> Dict[str, Any]:
        vals = self.values
        rets = self.returns if len(self.values) > 1 else np.array([])
        return {
            "name": self.name,
            "observations": self.n_observations,
            "start": str(self.dates[0]) if len(self.dates) > 0 else None,
            "end": str(self.dates[-1]) if len(self.dates) > 0 else None,
            "frequency": self.frequency,
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "mean_return": float(np.mean(rets)) if len(rets) > 0 else None,
            "volatility": float(np.std(rets)) if len(rets) > 0 else None,
            "skewness": float(pd.Series(rets).skew()) if len(rets) > 3 else None,
            "kurtosis": float(pd.Series(rets).kurtosis()) if len(rets) > 4 else None,
        }


class QuantDataManager:
    """
    Manages quantitative data: ingests scraped results, files, or manual input
    and converts them into TimeSeriesData objects for analysis.
    """

    def __init__(self):
        self._datasets: Dict[str, TimeSeriesData] = {}

    def add_from_dataframe(
        self,
        name: str,
        df: pd.DataFrame,
        value_column: str = "close",
        date_column: str = "date",
        frequency: str = "daily",
        **metadata
    ) -> TimeSeriesData:
        """Add a time-series from a pandas DataFrame."""
        df_clean = df.copy()
        # Ensure value column is numeric
        if value_column in df_clean.columns:
            df_clean[value_column] = pd.to_numeric(df_clean[value_column], errors="coerce")
            df_clean = df_clean.dropna(subset=[value_column])
        # Ensure date column if present
        if date_column in df_clean.columns:
            df_clean[date_column] = pd.to_datetime(df_clean[date_column], errors="coerce")
            df_clean = df_clean.dropna(subset=[date_column])
            df_clean = df_clean.sort_values(date_column).reset_index(drop=True)

        tsd = TimeSeriesData(
            name=name,
            df=df_clean.reset_index(drop=True),
            value_column=value_column,
            date_column=date_column,
            frequency=frequency,
            metadata=metadata,
        )
        self._datasets[name] = tsd
        return tsd

    def add_from_scraped_results(
        self,
        name: str,
        results: List[Dict[str, Any]],
        value_key: str,
        date_key: Optional[str] = None,
        frequency: str = "daily",
        **metadata
    ) -> Optional[TimeSeriesData]:
        """
        Convert scraped results (list of dicts) into a TimeSeriesData object.
        Automatically detects numeric columns and date columns.
        """
        if not results:
            return None

        df = pd.DataFrame(results)

        # Remove internal columns
        internal_cols = ["_url", "_scraped_at"]
        for col in internal_cols:
            if col in df.columns:
                if date_key is None and col == "_scraped_at":
                    date_key = col
                df = df.drop(columns=[col])

        # Auto-detect date column if not specified
        if date_key is None:
            for col in df.columns:
                if "date" in col.lower() or "time" in col.lower() or "تاریخ" in col.lower():
                    date_key = col
                    break

        # Auto-detect value column
        if value_key not in df.columns:
            # Try to find the most numeric column
            for col in df.columns:
                if col == date_key:
                    continue
                try:
                    numeric_vals = pd.to_numeric(df[col], errors="coerce")
                    if numeric_vals.notna().mean() > 0.7:
                        value_key = col
                        break
                except Exception:
                    continue

        return self.add_from_dataframe(
            name=name, df=df, value_column=value_key,
            date_column=date_key or "", frequency=frequency, **metadata,
        )

    def add_from_csv(
        self, name: str, filepath: str,
        value_column: str = "close",
        date_column: str = "date",
        frequency: str = "daily",
        **kwargs
    ) -> TimeSeriesData:
        """Load time-series from a CSV file."""
        df = pd.read_csv(filepath, **kwargs)
        return self.add_from_dataframe(
            name=name, df=df, value_column=value_column,
            date_column=date_column, frequency=frequency,
        )

    def add_from_lists(
        self,
        name: str,
        values: List[float],
        dates: Optional[List[Union[str, datetime]]] = None,
        frequency: str = "daily",
        **metadata
    ) -> TimeSeriesData:
        """Add a time-series from simple lists of values and optional dates."""
        data = {"value": values}
        if dates:
            data["date"] = dates
        df = pd.DataFrame(data)
        return self.add_from_dataframe(
            name=name, df=df, value_column="value",
            date_column="date" if dates else "",
            frequency=frequency, **metadata,
        )

    def add_multivariate_from_dataframe(
        self,
        name: str,
        df: pd.DataFrame,
        value_columns: List[str],
        date_column: str = "date",
        frequency: str = "daily",
        **metadata
    ) -> Dict[str, TimeSeriesData]:
        """Add multiple time-series from columns of a single DataFrame."""
        result = {}
        for col in value_columns:
            if col in df.columns:
                tsd = self.add_from_dataframe(
                    name=f"{name}_{col}", df=df[[date_column, col]] if date_column in df.columns else df[[col]],
                    value_column=col, date_column=date_column, frequency=frequency, **metadata,
                )
                result[col] = tsd
        return result

    def get_dataset(self, name: str) -> Optional[TimeSeriesData]:
        return self._datasets.get(name)

    def list_datasets(self) -> List[str]:
        return list(self._datasets.keys())

    def remove_dataset(self, name: str) -> bool:
        if name in self._datasets:
            del self._datasets[name]
            return True
        return False

    def get_all_values(self) -> Dict[str, np.ndarray]:
        return {name: tsd.values for name, tsd in self._datasets.items()}

    def get_returns_matrix(self) -> Tuple[pd.DataFrame, List[str]]:
        """Build a aligned returns DataFrame from all datasets."""
        series_dict = {}
        names = []
        for name, tsd in self._datasets.items():
            rets = tsd.returns
            if len(rets) > 0:
                series_dict[name] = pd.Series(rets, name=name)
                names.append(name)
        if not series_dict:
            return pd.DataFrame(), []
        # Align to shortest length
        min_len = min(len(s) for s in series_dict.values())
        for k in series_dict:
            series_dict[k] = series_dict[k].iloc[-min_len:]
        return pd.DataFrame(series_dict), names

    def get_price_matrix(self) -> Tuple[pd.DataFrame, List[str]]:
        """Build a aligned price DataFrame from all datasets."""
        series_dict = {}
        names = []
        for name, tsd in self._datasets.items():
            vals = tsd.values
            series_dict[name] = pd.Series(vals, name=name)
            names.append(name)
        if not series_dict:
            return pd.DataFrame(), []
        min_len = min(len(s) for s in series_dict.values())
        for k in series_dict:
            series_dict[k] = series_dict[k].iloc[-min_len:]
        return pd.DataFrame(series_dict), names

    def generate_sample_data(self, name: str, n: int = 500,
                              start_price: float = 100.0,
                              mu: float = 0.0005, sigma: float = 0.02,
                              frequency: str = "daily") -> TimeSeriesData:
        """Generate sample GBM price data for testing."""
        np.random.seed(42)
        returns = np.random.normal(mu, sigma, n)
        prices = start_price * np.exp(np.cumsum(returns))
        dates = pd.date_range(end=datetime.now(), periods=n, freq="B")
        return self.add_from_lists(name=name, values=prices.tolist(),
                                   dates=dates.strftime("%Y-%m-%d").tolist(),
                                   frequency=frequency, source="generated")

    def clear_all(self) -> None:
        self._datasets.clear()
