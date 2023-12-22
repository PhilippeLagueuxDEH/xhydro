# Created on Tue Dec 12 21:55:25 2023
# @author: Richard Arsenault
"""Objective function package for xhydro, for calibration and model evaluation

This package provides a flexible suite of popular objective function metrics in
hydrological modelling and hydrological model calibration. The main function
'get_objective_function' returns the value of the desired objective function
while allowing users to customize many aspects:

    1-  Select the objective function to run;
    2-  Allow providing a mask to remove certain elements from the objective
    function calculation (e.g. for odd/even year calibration, or calibration
    on high or low flows only, or any custom setup).
    3-  Apply a transformation on the flows to modify the behaviour of the
    objective function calculation (e.g taking the log, inverse or square
    root transform of the flows before computing the objective function).

This function also contains some tools and inputs reserved for the calibration
toolbox, such as the ability to take the negative of the objective function to
maximize instead of minimize a metric according to the needs of the optimizing
algorithm.
"""

import sys

# Import packages
import numpy as np


def get_objective_function(
    Qobs,
    Qsim,
    obj_func="rmse",
    take_negative=False,
    mask=None,
    transform=None,
    epsilon=None,
):
    """
    Entrypoint function for the objective function calculation. More can be
    added by adding the function to this file and adding the option in this
    function.

    NOTE: All data corresponding to NaN values in the observation set are
          removed from the calculation. If a mask is passed, it must be the
          same size as the Qsim and Qobs vectors. If any NaNs are present in
          the Qobs dataset, all corresponding data in the Qobs, Qsim and mask
          will be removed prior to passing to the processing function.

    Parameters
    ----------
    Qobs: numpy array of size n
        Vector containing the Observed streamflow to be used in the objective
        function calculation. It is the target to attain.

    Qsim: numpy array of size n
        Vector containing the Simulated streamflow as generated by the hydro-
        logical model. It is modified by changing parameters and resumulating
        the hydrological model.

    obj_func : string, optional
        String representing the objective function to use in the calibration.
        Options must be one of the accepted objective functions:

            - "abs_bias" : Absolute value of the "bias" metric
            - "abs_pbias": Absolute value of the "pbias" metric
            - "abs_volume_error" : Absolute value of the volume_error metric
            - "agreement_index": Index of agreement
            - "bias" : Bias metric
            - "correlation_coeff": Correlation coefficient
            - "kge" : Kling Gupta Efficiency metric (2009 version)
            - "kge_mod" : Kling Gupta Efficiency metric (2012 version)
            - "mae": Mean Absolute Error metric
            - "mare": Mean Absolute Relative Error metric
            - "mse" : Mean Square Error metric
            - "nse": Nash-Sutcliffe Efficiency metric
            - "pbias" : Percent bias (relative bias)
            - "r2" : r-squared, i.e. square of correlation_coeff.
            - "rmse" : Root Mean Square Error
            - "rrmse" : Relative Root Mean Square Error (RMSE-to-mean ratio)
            - "rsr" : Ratio of RMSE to standard deviation.
            - "volume_error": Total volume error over the period.

        The default is 'rmse'.

    take_negative : Boolean used to force the objective function to be
        multiplied by minus one (-1) such that it is possible to maximize it
        if the optimizer is a minimizer and vice-versa. Should always be set
        to False unless required by an optimization setup, which is handled
        internally and transparently to the user.

        The default is False.

    mask : numpy array (vector) of size n, optional
        array of 0 or 1 on which the objective function should be applied.
        Values of 1 indicate that the value is included in the calculation, and
        values of 0 indicate that the value is excluded and will have no impact
        on the objective function calculation. This can be useful for specific
        optimization strategies such as odd/even year calibration, seasonal
        calibration or calibration based on high/low flows.

        The default is None, and all data are preserved.

    transform : string indicating the type of transformation required. Can be
        one of the following values:

            - "sqrt" : Square root transformation of the flows [sqrt(Q)]
            - "log" : Logarithmic transformation of the flows [log(Q)]
            - "inv" : Inverse transformation of the flows [1/Q]

        The default value is "None", by which no transformation is performed.

    epsilon: scalar float indicating the perturbation to add to the flow
        time series during a transformation to avoid division by zero and
        logarithmic transformation. The perturbation is equal to:

            perturbation = epsilon * mean(Qobs)

        The default value is 0.01.


    NOTE: All data corresponding to NaN values in the observation set are
          removed from the calculation

    Returns
    -------
    obj_fun_val: scalar float representing the value of the selected objective
    function (obj_fun).
    """
    # List of available objective functions
    obj_func_list = [
        "abs_bias",
        "abs_pbias",
        "abs_volume_error",
        "agreement_index",
        "bias",
        "correlation_coeff",
        "kge",
        "kge_mod",
        "mae",
        "mare",
        "mse",
        "nse",
        "pbias",
        "r2",
        "rmse",
        "rrmse",
        "rsr",
        "volume_error",
    ]

    # Basic error checking
    if Qobs.shape[0] != Qsim.shape[0]:
        sys.exit("Observed and Simulated flows are not of the same size.")

    # Check mask size and contents
    if mask is not None:
        # Size
        if Qobs.shape[0] != mask.shape[0]:
            sys.exit("Mask is not of the same size as the streamflow data.")

        # All zero or one?
        if not np.setdiff1d(np.unique(mask), np.array([0, 1])).size == 0:
            sys.exit("Mask contains values other 0 or 1. Please modify.")

    # Check that the objective function is in the list of available methods
    if obj_func not in obj_func_list:
        sys.exit(
            "Selected objective function is currently unavailable. "
            + "Consider contributing to our project at: "
            + "github.com/hydrologie/xhydro"
        )

    # Ensure there are no NaNs in the dataset
    if mask is not None:
        mask = mask[~np.isnan(Qobs)]
    Qsim = Qsim[~np.isnan(Qobs)]
    Qobs = Qobs[~np.isnan(Qobs)]

    # Apply mask before trasform
    if mask is not None:
        Qsim = Qsim[mask == 1]
        Qobs = Qobs[mask == 1]
        mask = mask[mask == 1]

    # Transform data if needed
    if transform is not None:
        Qsim, Qobs = transform_flows(Qsim, Qobs, transform, epsilon)

    # Compute objective function by switching to the correct algorithm
    match obj_func:
        case "abs_bias":
            obj_fun_val = abs_bias(Qsim, Qobs)
        case "abs_pbias":
            obj_fun_val = abs_pbias(Qsim, Qobs)
        case "abs_volume_error":
            obj_fun_val = abs_volume_error(Qsim, Qobs)
        case "agreement_index":
            obj_fun_val = agreement_index(Qsim, Qobs)
        case "bias":
            obj_fun_val = bias(Qsim, Qobs)
        case "correlation_coeff":
            obj_fun_val = correlation_coeff(Qsim, Qobs)
        case "kge":
            obj_fun_val = kge(Qsim, Qobs)
        case "kge_mod":
            obj_fun_val = kge_mod(Qsim, Qobs)
        case "mae":
            obj_fun_val = mae(Qsim, Qobs)
        case "mare":
            obj_fun_val = mare(Qsim, Qobs)
        case "mse":
            obj_fun_val = mse(Qsim, Qobs)
        case "nse":
            obj_fun_val = nse(Qsim, Qobs)
        case "pbias":
            obj_fun_val = pbias(Qsim, Qobs)
        case "r2":
            obj_fun_val = r2(Qsim, Qobs)
        case "rmse":
            obj_fun_val = rmse(Qsim, Qobs)
        case "rrmse":
            obj_fun_val = rrmse(Qsim, Qobs)
        case "rsr":
            obj_fun_val = rsr(Qsim, Qobs)
        case "volume_error":
            obj_fun_val = volume_error(Qsim, Qobs)

    # Take the negative value of the Objective Function to return to the
    # optimizer.
    if take_negative:
        obj_fun_val = obj_fun_val * -1

    print(obj_fun_val)

    return obj_fun_val


def get_objfun_minimize_or_maximize(obj_func):
    """
    Checks the name of the objective function and returns whether it should be
    maximized or minimized. Returns a boolean value, where True means it should
    be maximized, and Flase means that it should be minimized. Objective
    functions other than those programmed here will raise an error.

    Inputs:
        obj_func: string containing the label for the desired objective
        function.
    """
    # Define metrics that need to be maximized:
    if obj_func in [
        "agreement_index",
        "correlation_coeff",
        "kge",
        "kge_mod",
        "nse",
        "r2",
    ]:
        maximize = True

    # Define the metrics that need to be minimized:
    elif obj_func in [
        "abs_bias",
        "abs_pbias",
        "abs_volume_error",
        "mae",
        "mare",
        "mse",
        "rmse",
        "rrmse",
        "rsr",
    ]:
        maximize = False

    # Check for the metrics that exist but cannot be used for optimization
    elif obj_func in ["bias", "pbias", "volume_error"]:
        sys.exit(
            "The bias, pbias and volume_error metrics cannot be minimized or maximized. \
                 Please use the abs_bias, abs_pbias and abs_volume_error instead."
        )
    else:
        sys.exit("The objective function is unknown.")

    return maximize


def get_optimizer_minimize_or_maximize(algorithm):
    """
    Finds the direction in which the optimizer searches. Some optimizers try to
    maximize the objective function value, and others try to minimize it. Since
    our objective functions include some that need to be maximized and others
    minimized, it is imperative to ensure that the optimizer/objective-function
    pair work in tandem.


    Inputs:
        algorithm: string containing the direction of the optimizer search
    """
    # Define metrics that need to be maximized:
    if algorithm in [
        "DDS",
    ]:
        maximize = True

    # Define the metrics that need to be minimized:
    elif algorithm in [
        "SCEUA",
    ]:
        maximize = False

    # Any other optimizer at this date
    else:
        sys.exit("The optimization algorithm is unknown.")

    return maximize


def transform_flows(Qsim, Qobs, transform=None, epsilon=0.01):
    """
    Transform flows before computing the objective function.

    It is used to transform flows such that the objective function is computed
    on a transformed flow metric rather than on the original units of flow
    (ex: inverse, log-transformed, square-root)

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)

    Qobs : Observed streamflow vector (numpy array)

    transform : string indicating the type of transformation required. Can be
        one of the following values:

            - "sqrt" : Square root transformation of the flows [sqrt(Q)]
            - "log" : Logarithmic transformation of the flows [log(Q)]
            - "inv" : Inverse transformation of the flows [1/Q]

        The default value is "None", by which no transformation is performed.

    epsilon: scalar float indicating the perturbation to add to the flow
        time series during a transformation to avoid division by zero and
        logarithmic transformation. The perturbation is equal to:

            perturbation = epsilon * mean(Qobs)

        The default value is 0.01.

    Returns
    -------
    Qsim, Qobs transformed according to the transformation function requested
    by the user in "transform". Qsim and Qobs are numpy arrays.
    """
    # Quick check
    if transform is not None:
        if transform not in ["log", "inv", "sqrt"]:
            sys.exit("Flow transformation method not recognized.")

    # Transform the flow series if required
    if transform == "log":  # log transformation
        epsilon = epsilon * np.nanmean(Qobs)
        Qobs, Qsim = np.log(Qobs + epsilon), np.log(Qsim + epsilon)

    elif transform == "inv":  # inverse transformation
        epsilon = epsilon * np.nanmean(Qobs)
        Qobs, Qsim = 1.0 / (Qobs + epsilon), 1.0 / (Qsim + epsilon)

    elif transform == "sqrt":  # square root transformation
        Qobs, Qsim = np.sqrt(Qobs), np.sqrt(Qsim)

    # Return the flows after transformation (or original if no transform)
    return Qsim, Qobs


"""
BEGIN OBJECTIVE FUNCTIONS DEFINITIONS
"""


def abs_bias(Qsim, Qobs):
    """
    absolute bias metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    abs_bias: positive scalar float representing the absolute value of the
    "bias" metric. This metric is useful when calibrating on the bias, because
    bias should aim to be 0 but can take large positive or negative values.
    Taking the absolute value of the bias will let the optimizer minimize
    the value to zero.

    The abs_bias should be MINIMIZED.
    """
    return np.abs(bias(Qsim, Qobs))


def abs_pbias(Qsim, Qobs):
    """
    absolute pbias metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    abs_pbias: positive scalar float representing the absolute value of the
    "pbias" metric. This metric is useful when calibrating on the pbias,
    because pbias should aim to be 0 but can take large positive or negative
    values. Taking the absolute value of the pbias will let the optimizer
    minimize the value to zero.

    The abs_pbias should be MINIMIZED.
    """
    return np.abs(bias(Qsim, Qobs))


def abs_volume_error(Qsim, Qobs):
    """
    absolute value of the volume error metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    abs_volume_error: positive scalar float representing the absolute value of
    the "volume_error" metric. This metric is useful when calibrating on the
    volume_error, because volume_error should aim to be 0 but can take large
    positive or negative values. Taking the absolute value of the volume_error
    will let the optimizer minimize the value to zero.

    The abs_volume_error should be MINIMIZED.
    """
    return np.abs(volume_error(Qsim, Qobs))


def agreement_index(Qsim, Qobs):
    """
    index of agreement metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    agreement_index: scalar float representing the agreement index of Willmott
    (1981). Varies between 0 and 1.

    The Agreement index should be MAXIMIZED.
    """
    # Decompose into clearer chunks
    a = np.sum((Qobs - Qsim) ** 2)
    b = np.abs(Qsim - np.mean(Qobs)) + np.abs(Qobs - np.mean(Qobs))
    c = np.sum(b**2)

    return 1 - (a / c)


def bias(Qsim, Qobs):
    """
    bias metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    bias: scalar float representing the bias in the simulation. Can be negative
    or positive and gives the average error between the observed and simulated
    flows. This interpretation uses the definition that a positive bias value
    means that the simulation overestimates the true value (as opposed to many
    other sources on bias calculations that use the contrary interpretation).

    BIAS SHOULD AIM TO BE ZERO AND SHOULD NOT BE USED FOR CALIBRATION. FOR
    CALIBRATION, USE "abs_bias" TO TAKE THE ABSOLUTE VALUE.
    """
    return np.mean(Qsim - Qobs)


def correlation_coeff(Qsim, Qobs):
    """
    correlation coefficient metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    correlation_coeff: scalar float representing the correlation coefficient.

    The correlation_coeff should be MAXIMIZED.
    """
    return np.corrcoef(Qobs, Qsim)[0, 1]


def kge(Qsim, Qobs):
    """
    Kling-Gupta efficiency metric (2009 version)

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    kge: scalar float representing the Kling-Gupta Efficiency (KGE) metric of
    2009. It can take values from -inf to 1 (best case).

    The KGE should be MAXIMIZED.
    """
    # This pops up a lot, precalculate.
    Qsim_mean = np.mean(Qsim)
    Qobs_mean = np.mean(Qobs)

    # Calculate the components of KGE
    r_num = np.sum((Qsim - Qsim_mean) * (Qobs - Qobs_mean))
    r_den = np.sqrt(np.sum((Qsim - Qsim_mean) ** 2) * np.sum((Qobs - Qobs_mean) ** 2))
    r = r_num / r_den
    a = np.std(Qsim) / np.std(Qobs)
    b = np.sum(Qsim) / np.sum(Qobs)

    # Calculate the KGE
    kge = 1 - np.sqrt((r - 1) ** 2 + (a - 1) ** 2 + (b - 1) ** 2)

    return kge


def kge_mod(Qsim, Qobs):
    """
    Kling-Gupta efficiency metric (2012 version)

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    kge_mod: scalar float representing the modified Kling-Gupta Efficiency
    (KGE) metric of 2012. It can take values from -inf to 1 (best case).

    The kge_mod should be MAXIMIZED.
    """
    # These pop up a lot, precalculate
    Qsim_mean = np.mean(Qsim)
    Qobs_mean = np.mean(Qobs)

    # Calc KGE components
    r_num = np.sum((Qsim - Qsim_mean) * (Qobs - Qobs_mean))
    r_den = np.sqrt(np.sum((Qsim - Qsim_mean) ** 2) * np.sum((Qobs - Qobs_mean) ** 2))
    r = r_num / r_den
    g = (np.std(Qsim) / Qsim_mean) / (np.std(Qobs) / Qobs_mean)
    b = np.mean(Qsim) / np.mean(Qobs)

    # Calc the modified KGE metric
    kge_mod = 1 - np.sqrt((r - 1) ** 2 + (g - 1) ** 2 + (b - 1) ** 2)

    return kge_mod


def mae(Qsim, Qobs):
    """
    mean absolute error metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    mae: scalar float representing the Mean Absolute Error. It can be
    interpreted as the average error (absolute) between observations and
    simulations for any time step.

    The mae should be MINIMIZED.
    """
    return np.mean(np.abs(Qsim - Qobs))


def mare(Qsim, Qobs):
    """
    mean absolute relative error metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    mare: scalar float representing the Mean Absolute Relative Error. For
    streamflow, where Qobs is always zero or positive, the MARE is always
    positive.

    The mare should be MINIMIZED.
    """
    return np.sum(np.abs(Qobs - Qsim)) / np.sum(Qobs)


def mse(Qsim, Qobs):
    """
    mean square error metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    mse: scalar float representing the Mean Square Error. It is the sum of
    squared errors for each day divided by the total number of days. Units are
    thus squared units, and the best possible value is 0.

    The mse should be MINIMIZED.
    """
    return np.mean((Qobs - Qsim) ** 2)


def nse(Qsim, Qobs):
    """
    Nash-Sutcliffe efficiency metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    nse: scalar float representing the Nash-Sutcliffe Efficiency (NSE) metric.
    It can take values from -inf to 1, with 0 being as good as using the mean
    observed flow as the estimator.

    The nse should be MAXIMIZED.
    """
    num = np.sum((Qobs - Qsim) ** 2)
    den = np.sum((Qobs - np.mean(Qobs)) ** 2)

    return 1 - (num / den)


def pbias(Qsim, Qobs):
    """
    percent bias metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    pbias: scalar float representing the Percent bias. Can be negative or
    positive and gives the average relative error between the observed and
    simulated flows. This interpretation uses the definition that a positive
    bias value means that the simulation overestimates the true value (as
    opposed to many other sources on bias calculations that use the contrary
    interpretation).

    PBIAS SHOULD AIM TO BE ZERO AND SHOULD NOT BE USED FOR CALIBRATION. FOR
    CALIBRATION, USE "abs_pbias" TO TAKE THE ABSOLUTE VALUE.
    """
    return (np.sum(Qsim - Qobs) / np.sum(Qobs)) * 100


def r2(Qsim, Qobs):
    """
    r-squred metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    r2: scalar float representing the r-squared (R2) metric equal to the square
    of the correlation coefficient.

    The r2 should be MAXIMIZED.
    """
    return correlation_coeff(Qsim, Qobs) ** 2


def rmse(Qsim, Qobs):
    """
    root mean square error metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    rmse: scalar float representing the Root Mean Square Error. Units are the
    same as the timeseries data (ex. m3/s). It can take zero or positive
    values.

    The rmse should be MINIMIZED.
    """
    return np.sqrt(np.mean((Qobs - Qsim) ** 2))


def rrmse(Qsim, Qobs):
    """
    relative root mean square error (ratio of rmse to mean) metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    rrmse: scalar float representing the ratio of the RMSE to the mean of the
    observations. It allows scaling RMSE values to compare results between
    time series of different magnitudes (ex. flows from small and large
    watersheds). Also known as the CVRMSE.

    The rrmse should be MINIMIZED.
    """
    return rmse(Qsim, Qobs) / np.mean(Qobs)


def rsr(Qsim, Qobs):
    """
    ratio of root mean square error to standard deviation metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    rsr: scalar float representing the Root Mean Square Error (RMSE) divided by
    the standard deviation of the observations. Also known as the "Ratio of the
    Root Mean Square Error to the Standard Deviation of Observations".

    The rsr should be MINIMIZED.
    """
    return rmse(Qobs, Qsim) / np.std(Qobs)


def volume_error(Qsim, Qobs):
    """
    volume error metric

    Parameters
    ----------
    Qsim : Simulated streamflow vector (numpy array)
    Qobs : Observed streamflow vector (numpy array)

    Returns
    -------
    volume_error: scalar float representing the total error in terms of volume
    over the entire period. Expressed in terms of the same units as input data,
    so for flow rates it is important to multiply by the duration of the time-
    step to obtain actual volumes.

    The volume_error should be MINIMIZED.
    """
    return np.sum(Qsim - Qobs) / np.sum(Qobs)


"""
ADD OBJECTIVE FUNCTIONS HERE
"""
