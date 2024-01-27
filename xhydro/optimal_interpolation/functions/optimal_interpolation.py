"""Package containing the optimal interpolation functions."""
from functools import partial

import numpy as np
from scipy.stats import norm

from .mathematical_algorithms import calculate_average_distance
from .utilities import initialize_nan_arrays


def optimal_interpolation(oi_input, args):
    """Perform the actual optimal interpolation step."""
    if len(args) == 0:
        args = {}

    estimated_count = (
        1 if len(oi_input["x_est"].shape) == 1 else oi_input["x_est"].shape[1]
    )
    observed_count = len(oi_input["x_obs"][0, :])
    oi_output = oi_input

    cond = 0

    if isinstance(args, dict):
        if "x_obs" in args:
            cond = (
                np.array_equal(args["x_est"], oi_input["x_est"])
                and np.array_equal(args["y_est"], oi_input["y_est"])
            ) and (
                np.array_equal(args["x_obs"], oi_input["x_obs"])
                and np.array_equal(args["y_obs"], oi_input["y_obs"])
            )
    if cond == 0:
        distance_obs_vs_obs = calculate_average_distance(
            oi_input["x_obs"], oi_input["y_obs"]
        )
    else:
        distance_obs_vs_obs = args["Doo"]

    args["x_obs"] = oi_input["x_obs"]
    args["y_obs"] = oi_input["y_obs"]
    args["Doo"] = distance_obs_vs_obs

    covariance_obs_vs_obs = oi_input["error_cov_fun"](distance_obs_vs_obs) / oi_input[
        "error_cov_fun"
    ](0)

    BEo_j = np.tile(oi_input["bg_var_obs"], (observed_count, 1))
    BEo_i = np.tile(
        np.resize(oi_input["bg_var_obs"], (1, observed_count)), (observed_count, 1)
    )

    Bij = covariance_obs_vs_obs * np.sqrt(BEo_j) / np.sqrt(BEo_i)

    OEo_j = np.tile(oi_input["var_obs"], (observed_count, 1))
    OEo_i = np.tile(oi_input["var_obs"], (1, observed_count))

    Oij = (np.sqrt(OEo_j) * np.sqrt(OEo_i)) * np.eye(len(OEo_j), len(OEo_j[0])) / BEo_i

    if cond == 0:
        distance_obs_vs_est = np.zeros((1, observed_count))
        x_est = oi_input["x_est"]
        y_est = oi_input["y_est"]

        for i in range(estimated_count):
            for j in range(observed_count // 2):
                distance_obs_vs_est[i, j] = np.mean(
                    np.sqrt(
                        np.power(oi_input["x_obs"][:, j] - x_est[:], 2)
                        + np.power(oi_input["y_obs"][:, j] - y_est[:], 2)
                    )
                )
                distance_obs_vs_est[i, -j - 1] = np.mean(
                    np.sqrt(
                        np.power(oi_input["x_obs"][:, -j - 1] - x_est[:], 2)
                        + np.power(oi_input["y_obs"][:, -j - 1] - y_est[:], 2)
                    )
                )
    else:
        distance_obs_vs_est = args["distance_obs_vs_est"]

    args["x_est"] = oi_input["x_est"]
    args["y_est"] = oi_input["y_est"]
    args["distance_obs_vs_est"] = distance_obs_vs_est

    BEe = np.tile(
        np.resize(oi_input["bg_var_est"], (1, observed_count)), (estimated_count, 1)
    )
    BEo = np.tile(oi_input["bg_var_obs"], (estimated_count, 1))

    Coe = oi_input["error_cov_fun"](distance_obs_vs_est) / oi_input["error_cov_fun"](0)

    Bei = np.resize(Coe * np.sqrt(BEe) / np.sqrt(BEo), (observed_count, 1))

    departures = oi_input["bg_departures"].reshape((1, len(oi_input["bg_departures"])))

    weights = np.linalg.solve(Bij + Oij, Bei)
    weights = weights.reshape((1, len(weights)))

    oi_output["v_est"] = oi_input["bg_est"] + np.sum(weights * departures)
    oi_output["var_est"] = oi_input["bg_var_est"] * (
        1 - np.sum(Bei[:, 0] * weights[0, :])
    )

    return oi_output, args


def loop_interpolation_optimale_stations(args):
    """Apply optimal interpolation to a single validation site for all times.

    Takes as input the "args" iterator values prepared just before, unzips them
    into its components, then runs the code for a single leave-one-out validation
    station. The order is controlled by the pool, so this function is run in
    parallel. Returns the desired quantiles to the pool.map that calls it.
    """
    # Get data from the args input
    (
        i,
        station_count,
        qobs_log,
        qsim_log,
        ecf_fun,
        par_opt,
        PX,
        PY,
        start_date,
        end_date,
        qobs_val,
        drainage_area,
        ratio_var_bg,
        percentiles,
        iterations,
    ) = args

    # Get the number of stations from the dataset
    index = range(0, station_count)

    # Get the number of simulation days
    time_range = (end_date - start_date).days

    # Define the exit vectors for a single catchment at a time since we will
    # work on stations in parallel.
    flow_quantiles = initialize_nan_arrays(time_range, len(percentiles))

    # Start cross-validation, getting indexes of the validation set.
    index_validation = i
    index_calibration = np.setdiff1d(index, index_validation)

    # Compute difference between the obs and sim log-transformed flows for the
    # calibration basins
    difference = qobs_log[:, index_calibration] - qsim_log[:, index_calibration]
    vsim_at_est = qsim_log[:, index_validation]

    # Create and update dictionary for the interpolation input data. This object
    # is updated later in the code and iterated, and updated. So keeps things
    # efficient this way.
    oi_input = {}
    oi_input.update(
        {
            "var_obs": ratio_var_bg,
            "error_cov_fun": partial(ecf_fun, par=par_opt),
            "x_est": PX[:, index_validation],
            "y_est": PY[:, index_validation],
        }
    )

    # Object with the arguments to the OI that is passed along at each time step
    # and updated. Named oi_args to not confuse with this functions' own args.
    oi_args = {}

    # For each timestep, build the interpolator and apply to the cross-
    # validation catchment.
    for j in range(time_range):
        # Need to skip days where no value exists for verification
        if not np.isnan(qobs_val[j, index_validation]):
            val = difference[j, :]
            idx = ~np.isnan(val)

            # Update the optimal interpolation dictionary.
            oi_input.update(
                {
                    "x_obs": PX[:, index_calibration[idx]],
                    "y_obs": PY[:, index_calibration[idx]],
                    "bg_departures": difference[j, idx],
                    "bg_var_obs": np.ones(idx.sum()),
                    "bg_est": vsim_at_est[j],
                    "bg_var_est": 1,
                }
            )

            # Apply the interpolator and get outputs
            oi_output, oi_args = optimal_interpolation(oi_input, oi_args)

            # Get variance properties
            var_bg = np.var(difference[j, idx])
            var_est = oi_output["var_est"] * var_bg

            # Get the percentile values for each desired percentile.
            vals = norm.ppf(percentiles, loc=oi_output["v_est"], scale=np.sqrt(var_est))

            # Get the values in real units and scale according to drainage area
            vals = np.exp(vals) * drainage_area[i]
            for k in range(0, len(percentiles)):
                flow_quantiles[k][j] = vals[k]

    # return the flow quantiles as desired.
    return flow_quantiles
