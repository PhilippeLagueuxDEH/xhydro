"""Hydrological modelling framework.

This collection of functions should serve as the main entry point for
hydrological modelling. The entire framework is based on the "model_config"
object. This object is meant to be a container that can be used as needed by
any hydrologic model. For example, it can store datasets directly, paths to
datasets (nc files or other), csv files, basically anything that can be stored
in a dictionary.

It then becomes the user's responsibility to ensure that required data for a
given model be provided in the model_config object both in the data preparation
stage and in the hydrological model implementation. This can be addressed by
a set of pre-defined codes for given model structures. This present package
(hydrological_modelling.py) should contain the logic to:

    1. From the model_config["model_name"] key, select the appropriate function
       (hydrological model) to run.
    2. Pass the model_config object to the correct hydrological modelling
       function.
    3. Parse the model_config object to extract required data for the given
       model, such as: parameters, meteorological data, paths to input files, and catchment characteristics as required
    4. Run the hydrological model with the given data
    5. Return the streamflow (Qsim).

This will make it very easy to add hydrological models, no matter their
complexity. It will also make it easy for newer Python users to implement
models as the logic is clearly exposed and does not make use of complex classes
or other dynamic objects. Models can be added here, and a specific routine
should also be defined to produce the required model_config for each model.

Once this is accomplished, running the model from a model_config object becomes
trivial and allows for easy calibration, regionalisation, analysis and any
other type of interaction.
"""

import numpy as np
import pandas as pd
import xarray as xr
import tempfile
from pathlib import Path

from ravenpy.config.emulators import (
    GR4JCN,
    HMETS,
    Mohyse,
    HBVEC,
    Blended,
    SACSMA,
    HYPR,
)
from ravenpy.config import commands as rc
from ravenpy import OutputReader
from ravenpy.ravenpy import run


__all__ = ["run_hydrological_model", "get_hydrological_model_inputs"]


def run_hydrological_model(model_config: dict):
    """Hydrological model selector.

    This is the main hydrological model selector. This is the code that looks
    at the "model_config["model_name"]" keyword and calls the appropriate
    hydrological model function.

    Parameters
    ----------
    model_config : dict
        The model configuration object that contains all info to run the model.
        The model function called to run this model shouls always use this object
        and read-in data it requires. It will be up to the user to provide the
        data that the model requires.

    Returns
    -------
    xr.Dataset
        Simulated streamflow from the model, in xarray Dataset format.
    """
    if model_config["model_name"] == "Dummy":
        qsim = _dummy_model(model_config)

    elif model_config["model_name"].lower() in ["gr4jcn", "hmets", "mohyse", "hbvec", "hypr", "sacsma", "blended"]:
        qsim = _ravenpy_model(model_config)

    elif model_config["model_name"] == "ADD_OTHER_HERE":
        # ADD OTHER MODELS HERE
        qsim = 0
    else:
        raise NotImplementedError(
            f"The model '{model_config['model_name']}' is not recognized."
        )

    return qsim


def get_hydrological_model_inputs(model_name: str):
    """Required hydrological model inputs for model_config objects.

    Parameters
    ----------
    model_name : str
        Model name that must be one of the models in the list of possible
        models.

    Returns
    -------
    dict
        Elements that must be found in the model_config object.
    """
    if model_name == "Dummy":
        required_config = dict(
            precip="Daily precipitation in mm.",
            temperature="Daily average air temperature in °C",
            drainage_area="Drainage area of the catchment, km²",
            parameters="Model parameters, length 3",
        )
    elif model_name.lower() in ["gr4jcn", "hmets", "mohyse", "hbvec", "hypr", "sacsma", "blended"]:
        # TODO ADD THIS
        required_config = dict(
            temperature="Daily average air temperature in °C.",
            precip="Daily precipitation in mm.",
            drainage_area="Drainage area of the catchment, km²",
        )
    elif model_name == "ADD_OTHER_HERE":
        # ADD OTHER MODELS HERE
        required_config = {}

    else:
        raise NotImplementedError(f"The model '{model_name}' is not recognized.")

    return required_config


def _dummy_model(model_config: dict):
    """Dummy model.

    Dummy model to show the implementation we should be aiming for. Each model
    will have its own required data that users can pass.

    Parameters
    ----------
    model_config : dict
        The model configuration object that contains all info to run the model.
        The model function called to run this model shouls always use this object
        and read-in data it requires. It will be up to the user to provide the
        data that the model requires.

    Returns
    -------
    xr.Dataset
        Simulated streamflow from the model, in xarray Dataset format.
    """
    # Parse the model_config object to extract required information
    precip = model_config["precip"]
    temperature = model_config["temperature"]
    area = model_config["drainage_area"]
    x = model_config["parameters"]

    # Run the dummy model using these data. Keeping it simple to calculate by
    # hand to ensure the calibration algorithm is working correctly and data
    # are handled correctly
    qsim = np.empty(len(precip))
    for t in range(0, len(precip)):
        qsim[t] = (precip[t] * x[0] + abs(temperature[t]) * x[1]) * x[2] * area

    # For this model, we can convert to xr.dataset by supposing dates. Other
    # models will require some dates in some form (to add to QC checks) in their
    # inputs.
    time = pd.date_range("2024-01-01", periods=len(precip))
    qsim = xr.Dataset(
        data_vars=dict(
            qsim=(["time"], qsim),
        ),
        coords=dict(time=time),
        attrs=dict(description="streamflow simulated by the Dummy Model"),
    )

    return qsim


def _ravenpy_model(model_config: dict):

    # Create HRU object for ravenpy based on catchment properties
    hru = dict(
        area=model_config["drainage_area"],
        elevation=model_config["elevation"],
        latitude=model_config["latitude"],
        longitude=model_config["longitude"],
        hru_type="land",
    )

    # Create the emulator configuration
    default_emulator_config = dict(
        HRUs=[hru],
        StartDate=model_config["start_date"],
        EndDate=model_config["end_date"],
        ObservationData=[rc.ObservationData.from_nc(model_config["qobs_path"], alt_names=model_config["alt_names_flow"])],
        Gauge=[
            rc.Gauge.from_nc(
                model_config["meteo_file"],  # Chemin d'accès au fichier contenant la météo
                data_type=model_config["data_type"],  # Liste de toutes les variables contenues dans le fichier
                alt_names=model_config["alt_names_meteo"],  # Mapping entre les noms des variables requises et celles dans le fichier.
                data_kwds=model_config["meteo_station_properties"],
            )
        ],
        RainSnowFraction="RAINSNOW_DINGMAN",
        Evaporation="PET_PRIESTLEY_TAYLOR",
    )

    model_name = model_config["model_name"].lower()

    if model_name == "gr4jcn":
        m = GR4JCN(params=model_config["parameters"], **default_emulator_config)
    elif model_name == "hmets":
        m = HMETS(params=model_config["parameters"], **default_emulator_config)
    elif model_name == "mohyse":
        m = Mohyse(params=model_config["parameters"], **default_emulator_config)
    elif model_name == "hbvec":
        default_emulator_config.pop("RainSnowFraction")
        m = HBVEC(params=model_config["parameters"], **default_emulator_config)
    elif model_name == "hypr":
        m = HYPR(params=model_config["parameters"], **default_emulator_config)
    elif model_name == "sacsma":
        m = SACSMA(params=model_config["parameters"], **default_emulator_config)
    elif model_name == "blended":
        m = Blended(params=model_config["parameters"], **default_emulator_config)
    else:
        raise ValueError("Hydrological model is an unknown Ravenpy variant.")

    workdir = Path(tempfile.mkdtemp(prefix="NB4"))
    m.write_rv(workdir=workdir)

    outputs_path = run(modelname="raven", configdir=workdir)
    outputs = OutputReader(path=outputs_path)

    qsim = xr.open_dataset(outputs.files["hydrograph"]).q_sim.to_dataset(name="qsim")

    if 'nbasins' in qsim.dims:
        qsim = qsim.squeeze()

    return qsim
