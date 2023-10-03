"""Local frequency analysis functions and utilities."""

import datetime
from typing import Union

import numpy as np
import scipy.stats
import statsmodels
import xarray as xr
import xclim.indices.stats
from statsmodels.tools import eval_measures

__all__ = [
    "fit",
    "parametric_quantiles",
    "criteria",
]


#     def view_criterions(self, var_of_interest):
#         """
#         Fonction to get Criterions results from a xhydro.Local object. Output is rounded for easiser visualisation.
#
#         Returns
#         -------
#         df : pd.Dataframe
#           Dataframe organised with id,	season,	year,	scipy_dist
#
#         Examples
#         --------
#         >>> import xarray as xr
#         >>> cehq_data_path = '/datasets/xhydro/tests/cehq/zarr'
#         >>> ds = xr.open_zarr(cehq_data_path, consolidated=True)
#         >>> donnees = Data(ds)
#         >>> donnees.get_maximum(tolerence=0.15, seasons=['Spring'])
#         >>> catchment_list = ['023301']
#         >>> sub_set = donnees.select_catchments(catchment_list = catchment_list)
#         >>> sub_set.season = ['Spring', 60, 182]
#         >>> return_period = np.array([1.01, 2, 2.33, 5, 10, 20, 50, 100, 200, 500, 1000, 10000])
#         >>> dist_list = ['expon', 'gamma', 'genextreme', 'genpareto', 'gumbel_r', 'pearson3', 'weibull_min']
#         >>> fa = xh.Local(data_ds = sub_set, return_period = return_period, dist_list = dist_list, tolerence = 0.15, seasons = ['Automne', 'Printemps'], min_year = 15)
#         >>> fa.view_quantiles()
#         >>> id	season	level_2	return_period	Quantiles
#             0	023301	Spring	expon	1.01	22.157376
#             1	023301	Spring	expon	2.00	87.891419
#             2	023301	Spring	expon	2.33	102.585536
#             3	023301	Spring	expon	5.00	176.052678
#             4	023301	Spring	expon	10.00	242.744095
#             ...
#         """
#         # dataarray to_dataframe uses first diemnsion as nameless index, so depending on the position in dim_order, dimension gets names level_x
#         var_list = [s for s in self.analyse_max.keys() if "criterions" in s]
#
#         if var_of_interest == "vol":
#             return (
#                 self.analyse_vol[var_list]
#                 .to_dataframe()
#                 .reset_index()[["id", "scipy_dist"] + var_list]
#                 .round()
#             )
#         elif var_of_interest == "max":
#             return (
#                 self.analyse_max[var_list]
#                 .to_dataframe()
#                 .reset_index()[["id", "season", "scipy_dist"] + var_list]
#                 .round()
#             )
#         else:
#             return print('use "vol" for volumes or "max" for maximums ')
#
#     def view_quantiles(self, var_of_interest):
#         """
#         Fonction to get Quantiles results from a xhydro.Local object.
#
#         Returns
#         -------
#         df : pd.Dataframe
#           Dataframe organised with id,	season,	year,	scipy_dist, return_period
#
#         Examples
#         --------
#         >>> import xarray as xr
#         >>> cehq_data_path = '/datasets/xhydro/tests/cehq/zarr'
#         >>> ds = xr.open_zarr(cehq_data_path, consolidated=True)
#         >>> donnees = Data(ds)
#         >>> donnees.get_maximum(tolerence=0.15, seasons=['Spring'])
#         >>> catchment_list = ['023301']
#         >>> sub_set = donnees.select_catchments(catchment_list = catchment_list)
#         >>> sub_set.season = ['Spring', 60, 182]
#         >>> return_period = np.array([1.01, 2, 2.33, 5, 10, 20, 50, 100, 200, 500, 1000, 10000])
#         >>> dist_list = ['expon', 'gamma', 'genextreme', 'genpareto', 'gumbel_r', 'pearson3', 'weibull_min']
#         >>> fa = xh.Local(data_ds = sub_set, return_period = return_period, dist_list = dist_list, tolerence = 0.15, seasons = ['Automne', 'Printemps'], min_year = 15)
#         >>> fa.view_criterions()
#         >>> id	season	level_2	Criterions
#         >>> 0	023301	Spring	expon	{'aic': 582.9252842821857, 'bic': 586.82777171...
#         >>> 1	023301	Spring	gamma	{'aic': 1739.77441499742, 'bic': 1745.62814615...
#             ...
#         """
#
#         var_list = [s for s in self.analyse_max.keys() if "quantiles" in s]
#         if var_of_interest == "vol":
#             return (
#                 self.analyse_vol[var_list]
#                 .to_dataframe()
#                 .reset_index()[
#                     ["id", "season", "scipy_dist", "return_period"] + var_list
#                 ]
#                 .round()
#             )
#         elif var_of_interest == "max":
#             return (
#                 self.analyse_max[var_list]
#                 .to_dataframe()
#                 .reset_index()[
#                     ["id", "season", "scipy_dist", "return_period"] + var_list
#                 ]
#                 .round()
#             )
#         else:
#             return print('use "vol" for volumes or "max" for maximums ')
#
#     def view_values(self, var_of_interest):
#         """
#         Fonction to get values results from a xhydro.Local object.
#
#         Returns
#         -------
#         df : pd.Dataframe
#           Dataframe organised with id,	season,	year,	scipy_dist, return_period
#
#         Examples
#         --------
#         >>> import xarray as xr
#         >>> cehq_data_path = '/datasets/xhydro/tests/cehq/zarr'
#         >>> ds = xr.open_zarr(cehq_data_path, consolidated=True)
#         >>> donnees = Data(ds)
#         >>> donnees.get_maximum(tolerence=0.15, seasons=['Spring'])
#         >>> catchment_list = ['023301']
#         >>> sub_set = donnees.select_catchments(catchment_list = catchment_list)
#         >>> sub_set.season = ['Spring', 60, 182]
#         >>> return_period = np.array([1.01, 2, 2.33, 5, 10, 20, 50, 100, 200, 500, 1000, 10000])
#         >>> dist_list = ['expon', 'gamma', 'genextreme', 'genpareto', 'gumbel_r', 'pearson3', 'weibull_min']
#         >>> fa = xh.Local(data_ds = sub_set, return_period = return_period, dist_list = dist_list, tolerence = 0.15, seasons = ['Automne', 'Printemps'], min_year = 15)
#         >>> fa.view_criterions()
#         >>> id	season	level_2	Criterions
#         >>> 0	023301	Spring	expon	{'aic': 582.9252842821857, 'bic': 586.82777171...
#         >>> 1	023301	Spring	gamma	{'aic': 1739.77441499742, 'bic': 1745.62814615...
#             ...
#         """
#         # TODO  Output as dict is ugly
#
#         if var_of_interest == "vol":
#             return self.analyse_vol[self.var_name].to_dataframe().dropna().reset_index()
#         elif var_of_interest == "max":
#             return (
#                 self.analyse_max[self.var_name]
#                 .to_dataframe()
#                 .reset_index()[
#                     ["id", "season", "time", "start_date", "end_date", self.var_name]
#                 ]
#                 .dropna()
#             )
#         else:
#             return print('use "vol" for volumes or "max" for maximums ')
#


class Local:
    def __init__(self, ds, **kwargs):
        """Local frequency analysis.

        Parameters
        ----------
        ds: xr.Dataset
            Dataset containing the yearly data to analyse.
        kwargs
            Keyword arguments passed to `fit`.
        """
        self.data = ds
        self.params = fit(ds, **kwargs)
        self.criteria = criteria(self.data, self.params)

    def parametric_quantiles(
        self, t: Union[float, list], mode: str = "max"
    ) -> xr.Dataset:
        return parametric_quantiles(self.params, t=t, mode=mode)


def fit(
    ds, distributions: list = None, min_years=None, method: str = "ML"
) -> xr.Dataset:
    """Fit multiple distributions to data.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset containing the data to fit. All variables will be fitted.
    distributions : list of str
        List of distribution names as defined in `scipy.stats`. See https://docs.scipy.org/doc/scipy/reference/stats.html#continuous-distributions.
        Defaults to ["expon", "gamma", "genextreme", "genpareto", "gumbel_r", "pearson3", "weibull_min"].
    min_years : int
        Minimum number of years required for a distribution to be fitted.
    method : str
        Fitting method. Defaults to "ML" (maximum likelihood).

    Returns
    -------
    xr.Dataset
        Dataset containing the parameters of the fitted distributions, with a new dimension `scipy_dist` containing the distribution names.

    Notes
    -----
    In order to combine the parameters of multiple distributions, the size of the `dparams` dimension is set to the maximum number of unique parameters between the distributions.
    """
    distributions = distributions or [
        "expon",
        "gamma",
        "genextreme",
        "genpareto",
        "gumbel_r",
        "pearson3",
        "weibull_min",
    ]
    out = []
    for v in ds.data_vars:
        p = []
        for d in distributions:
            p.append(
                xclim.indices.stats.fit(
                    ds[v].chunk({"time": -1}), dist=d, method=method
                )
                .assign_coords(scipy_dist=d)
                .expand_dims("scipy_dist")
            )
        params = xr.concat(p, dim="scipy_dist")

        # Reorder dparams to match the order of the parameters across all distributions, since subsequent operations rely on this.
        p_order = [list(pi.dparams.values) for pi in p]
        if any(len(pi) != 2 and len(pi) != 3 for pi in p_order):
            raise NotImplementedError(
                "Only distributions with 2 or 3 parameters are currently supported."
            )
        skew = np.unique([pi[0] for pi in p_order if len(pi) == 3])
        loc = np.unique([pi[0] if len(pi) == 2 else pi[1] for pi in p_order])
        scale = np.unique([pi[1] if len(pi) == 2 else pi[2] for pi in p_order])
        # if any common name between skew, loc and scale, raise error
        if (
            any([lo in skew for lo in loc])
            or any([s in skew for s in scale])
            or any([s in loc for s in scale])
        ):
            raise ValueError("Guessed skew, loc, and scale parameters are not unique.")
        params = params.sel(dparams=np.concatenate([skew, loc, scale]))

        # Check that it worked by making sure that the index is in ascending order
        for pi in p:
            p_order = [list(params.dparams.values).index(p) for p in pi.dparams.values]
            if not np.all(np.diff(p_order) > 0):
                raise ValueError(
                    "Something went wrong when ordering the parameters across distributions."
                )

        if min_years is not None:
            params = params.where(ds[v].notnull().sum("time") >= min_years)
        params.attrs["scipy_dist"] = distributions
        params.attrs["description"] = "Parameters of the distributions"
        params.attrs["long_name"] = "Distribution parameters"
        params.attrs["min_years"] = min_years
        out.append(params)

    out = xr.merge(out)
    out.attrs = ds.attrs

    return out


def parametric_quantiles(p, t: Union[float, list], mode: str = "max") -> xr.Dataset:
    """Compute quantiles from fitted distributions.

    Parameters
    ----------
    p : xr.Dataset
        Dataset containing the parameters of the fitted distributions.
        Must have a dimension `dparams` containing the parameter names and a dimension `scipy_dist` containing the distribution names.
    t : float or list of float
        Return period(s) in years.
    mode : {'max', 'min'}
        Whether the return period is the probability of exceedance (max) or non-exceedance (min).

    Returns
    -------
    xr.Dataset
        Dataset containing the quantiles of the distributions.
    """
    distributions = list(p["scipy_dist"].values)

    t = np.atleast_1d(t)
    if mode == "max":
        t = 1 - 1.0 / t
    elif mode == "min":
        t = 1.0 / t
    else:
        raise ValueError(f"'mode' must be 'max' or 'min', got '{mode}'.")

    out = []
    for v in p.data_vars:
        quantiles = []
        for d in distributions:
            da = (
                p[v]
                .sel(scipy_dist=d)
                .dropna("dparams", how="all")
                .transpose("dparams", ...)
            )
            da.attrs["scipy_dist"] = d
            q = (
                xclim.indices.stats.parametric_quantile(da, q=t)
                .rename({"quantile": "return_period"})
                .assign_coords(scipy_dist=d)
                .expand_dims("scipy_dist")
            )
            quantiles.append(q)
        quantiles = xr.concat(quantiles, dim="scipy_dist")
        quantiles.attrs["scipy_dist"] = distributions
        quantiles.attrs[
            "description"
        ] = "Quantiles estimated by statistic distributions"
        quantiles.attrs["long_name"] = "Distribution quantiles"
        out.append(quantiles)

    out = xr.merge(out)
    out.attrs = p.attrs

    return out


def criteria(ds, p) -> xr.Dataset:
    """Compute information criteria (AIC, BIC, AICC) from fitted distributions, using the log-likelihood.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset containing the yearly data that was fitted.
    p : xr.Dataset
        Dataset containing the parameters of the fitted distributions.
        Must have a dimension `dparams` containing the parameter names and a dimension `scipy_dist` containing the distribution names.

    Returns
    -------
    xr.Dataset
        Dataset containing the information criteria for the distributions.
    """

    def _get_criteria_1d(da, params, dist):
        da = np.atleast_2d(da).T
        params = np.atleast_2d(params).T

        llf = np.nansum(dist.logpdf(da, *params), axis=0)  # log-likelihood
        nobs = np.sum(np.isfinite(da), axis=0)
        df_modelwc = len(p)
        dof_eff = nobs - df_modelwc - 1.0

        aic = eval_measures.aic(llf=llf, nobs=nobs, df_modelwc=len(p))
        bic = eval_measures.bic(llf=llf, nobs=nobs, df_modelwc=len(p))
        # Custom AICC, because the one in statsmodels does not support multiple dimensions
        aicc = np.where(
            dof_eff > 0, -2.0 * llf + 2.0 * df_modelwc * nobs / dof_eff, np.nan
        )

        return np.stack([aic, bic, aicc], axis=1)

    out = []
    distributions = list(p["scipy_dist"].values)

    common_vars = list(set(ds.data_vars).intersection(p.data_vars))
    for v in common_vars:
        c = []
        for d in distributions:
            da = ds[v].transpose("time", ...)
            params = (
                p[v]
                .sel(scipy_dist=d)
                .dropna("dparams", how="all")
                .transpose("dparams", ...)
            )
            dist_obj = getattr(scipy.stats, d)

            crit = xr.apply_ufunc(
                _get_criteria_1d,
                da,
                params,
                kwargs={"dist": dist_obj},
                input_core_dims=[["time"], ["dparams"]],
                output_core_dims=[["criterion"]],
                dask_gufunc_kwargs=dict(output_sizes={"criterion": 3}),
                dask="parallelized",
            )

            # Add attributes
            crit = crit.assign_coords(criterion=["aic", "bic", "aicc"]).expand_dims(
                "scipy_dist"
            )
            crit.attrs = p[v].attrs
            crit.attrs["history"] = (
                crit.attrs.get("history", "")
                + f", [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] criteria: computed AIC, BIC and AICC. - statsmodels version: {statsmodels.__version__}"
            )
            crit.attrs[
                "description"
            ] = "Information criteria for the distribution parameters."
            crit.attrs["long_name"] = "Information criteria"

            # Remove a few attributes that are not relevant anymore
            crit.attrs.pop("method", None)
            crit.attrs.pop("estimator", None)
            crit.attrs.pop("min_years", None)
            c.append(crit)

        c = xr.concat(c, dim="scipy_dist")
        out.append(c)

    out = xr.merge(out)
    out.attrs = ds.attrs

    return out
