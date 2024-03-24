"""Test suite for hydrological modelling in hydrological_modelling.py"""

import datetime as dt
from copy import deepcopy

import numpy as np
import pytest
import xarray as xr

from xhydro.modelling import get_hydrological_model_inputs, hydrological_model


class TestHydrologicalModelling:
    def test_hydrological_modelling(self):
        """Test the hydrological models as they become online"""
        # Test the dummy model
        model_config = {
            "precip": np.array([10, 11, 12, 13, 14, 15]),
            "temperature": np.array([10, 3, -5, 1, 15, 0]),
            "qobs": np.array([120, 130, 140, 150, 160, 170]),
            "drainage_area": np.array([10]),
            "model_name": "Dummy",
            "parameters": np.array([5, 5, 5]),
        }
        qsim = hydrological_model(model_config).run()
        np.testing.assert_array_equal(qsim["streamflow"].values[3], 3500.00)

    def test_import_unknown_model(self):
        """Test for unknown model"""
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            model_config = {"model_name": "fake_model"}
            _ = hydrological_model(model_config).run()
            assert pytest_wrapped_e.type == NotImplementedError

    def test_missing_name(self):
        with pytest.raises(ValueError, match="The model name must be provided"):
            model_config = {"parameters": [1, 2, 3]}
            hydrological_model(model_config).run()


class TestHydrologicalModelRequirements:
    def test_get_unknown_model_requirements(self):
        """Test for required inputs for models with unknown name"""
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            model_name = "fake_model"
            _ = get_hydrological_model_inputs(model_name)
            assert pytest_wrapped_e.type == NotImplementedError

    @pytest.mark.parametrize("model_name", ["Dummy", "Hydrotel"])
    def test_get_model_requirements(self, model_name):
        """Test for required inputs for models"""
        expected_keys = {"Dummy": (6, 6), "Hydrotel": (8, 3)}

        all_config, _ = get_hydrological_model_inputs(model_name)
        assert len(all_config.keys()) == expected_keys[model_name][0]

        all_config, _ = get_hydrological_model_inputs(model_name, required_only=True)
        assert len(all_config.keys()) == expected_keys[model_name][1]


class TestRavenpyModels:
    """Test configurations of RavenPy models."""

    # List of types of data provided to Raven in the meteo file
    data_type = ["TEMP_MAX", "TEMP_MIN", "PRECIP"]

    # Alternate names in the netcdf file (for variables that have different names, map to the name in the file).
    alt_names_meteo = {"TEMP_MIN": "tmin", "TEMP_MAX": "tmax", "PRECIP": "pr"}
    alt_names_flow = "qobs"

    qobs_path = "/home/richard/src/xhydro/xhydro/tests/Debit_Riviere_Rouge.nc"

    start_date = dt.datetime(1985, 1, 1)
    end_date = dt.datetime(1990, 1, 1)

    model_config = {
        "meteo_file": "/home/richard/src/xhydro/xhydro/tests/ERA5_Riviere_Rouge_global.nc",
        "qobs_path": qobs_path,
        "qobs": xr.open_dataset(qobs_path)
        .qobs.sel(time=slice(start_date, end_date))
        .values,
        "drainage_area": np.array([100.0]),
        "elevation": np.array([250.5]),
        "latitude": np.array([46.0]),
        "longitude": np.array([-80.75]),
        "start_date": start_date,
        "end_date": end_date,
        "data_type": data_type,
        "alt_names_meteo": alt_names_meteo,
        "alt_names_flow": alt_names_flow,
    }

    # Station properties. Using the same as for the catchment, but could be different.
    meteo_station_properties = {
        "ALL": {
            "elevation": model_config["elevation"],
            "latitude": model_config["latitude"],
            "longitude": model_config["longitude"],
        }
    }

    model_config.update({"meteo_station_properties": meteo_station_properties})

    def test_ravenpy_gr4jcn(self):
        """Test for GR4JCN ravenpy model"""
        model_config = deepcopy(self.model_config)
        model_config.update(
            {
                "model_name": "gr4jcn",
                "parameters": [0.529, -3.396, 407.29, 1.072, 16.9, 0.947],
            }
        )

        qsim = run_hydrological_model(model_config)

        assert qsim["qsim"].shape == (1827,)

    def test_ravenpy_hmets(self):
        """Test for HMETS ravenpy model"""
        model_config = deepcopy(self.model_config)
        model_config.update(
            {
                "model_name": "hmets",
                "parameters": [
                    9.5019,
                    0.2774,
                    6.3942,
                    0.6884,
                    1.2875,
                    5.4134,
                    2.3641,
                    0.0973,
                    0.0464,
                    0.1998,
                    0.0222,
                    -1.0919,
                    2.6851,
                    0.3740,
                    1.0000,
                    0.4739,
                    0.0114,
                    0.0243,
                    0.0069,
                    310.7211,
                    916.1947,
                ],
            }
        )

        qsim = run_hydrological_model(model_config)

        assert qsim["qsim"].shape == (1827,)

    def test_ravenpy_mohyse(self):
        """Test for MOHYSE ravenpy model"""
        model_config = deepcopy(self.model_config)
        model_config.update(
            {
                "model_name": "mohyse",
                "parameters": [
                    1.0,
                    0.0468,
                    4.2952,
                    2.658,
                    0.4038,
                    0.0621,
                    0.0273,
                    0.0453,
                    0.9039,
                    5.6167,
                ],
            }
        )

        qsim = run_hydrological_model(model_config)

        assert qsim["qsim"].shape == (1827,)

    @pytest.mark.skip(
        reason="Weird error with negative simulated PET in ravenpy for HBVEC."
    )
    def test_ravenpy_hbvec(self):
        """Test for HBV-EC ravenpy model"""
        model_config = deepcopy(self.model_config)
        model_config.update(
            {
                "model_name": "hbvec",
                "parameters": [
                    0.059,
                    4.072,
                    2.002,
                    0.035,
                    0.10,
                    0.506,
                    3.44,
                    38.32,
                    0.46,
                    0.063,
                    2.278,
                    4.87,
                    0.57,
                    0.045,
                    0.878,
                    18.941,
                    2.037,
                    0.445,
                    0.677,
                    1.141,
                    1.024,
                ],
            }
        )

        qsim = run_hydrological_model(model_config)

        assert qsim["qsim"].shape == (1827,)

    @pytest.mark.skip(
        reason="Weird error with negative simulated PET in ravenpy for HYPR."
    )
    def test_ravenpy_hypr(self):
        """Test for HYPR ravenpy model"""
        model_config = deepcopy(self.model_config)
        model_config.update(
            {
                "model_name": "hypr",
                "parameters": [
                    -0.186,
                    2.92,
                    0.031,
                    0.439,
                    0.465,
                    0.117,
                    13.1,
                    0.404,
                    1.21,
                    59.1,
                    0.166,
                    4.10,
                    0.822,
                    41.5,
                    5.85,
                    0.69,
                    0.924,
                    1.64,
                    1.59,
                    2.51,
                    1.14,
                ],
            }
        )

        qsim = run_hydrological_model(model_config)

        assert qsim["qsim"].shape == (1827,)

    def test_ravenpy_sacsma(self):
        """Test for SAC-SMA ravenpy model"""
        model_config = deepcopy(self.model_config)
        model_config.update(
            {
                "model_name": "sacsma",
                "parameters": [
                    0.01,
                    0.05,
                    0.3,
                    0.05,
                    0.05,
                    0.13,
                    0.025,
                    0.06,
                    0.06,
                    1.0,
                    40.0,
                    0.0,
                    0.0,
                    0.1,
                    0.0,
                    0.01,
                    1.5,
                    0.482,
                    4.1,
                    1.0,
                    1.0,
                ],
            }
        )

        qsim = run_hydrological_model(model_config)

        assert qsim["qsim"].shape == (1827,)

    def test_ravenpy_blended(self):
        """Test for Blended ravenpy model"""
        model_config = deepcopy(self.model_config)
        model_config.update(
            {
                "model_name": "blended",
                "parameters": [
                    0.029,
                    2.21,
                    2.16,
                    0.00023,
                    21.74,
                    1.56,
                    6.21,
                    0.91,
                    0.035,
                    0.25,
                    0.00022,
                    1.214,
                    0.0473,
                    0.207,
                    0.078,
                    -1.34,
                    0.22,
                    3.84,
                    0.29,
                    0.483,
                    4.1,
                    12.83,
                    0.594,
                    1.65,
                    1.71,
                    0.372,
                    0.0712,
                    0.019,
                    0.408,
                    0.94,
                    -1.856,
                    2.36,
                    1.0,
                    1.0,
                    0.0075,
                    0.53,
                    0.0289,
                    0.961,
                    0.613,
                    0.956,
                    0.101,
                    0.0928,
                    0.747,
                ],
            }
        )

        qsim = run_hydrological_model(model_config)

        assert qsim["qsim"].shape == (1827,)


def test_streamflow(self):
    model_config = {
        "model_name": "Dummy",
        "precip": np.array([10, 11, 12, 13, 14, 15]),
        "temperature": np.array([10, 3, -5, 1, 15, 0]),
        "qobs": np.array([120, 130, 140, 150, 160, 170]),
        "drainage_area": np.array([10]),
        "parameters": np.array([5, 5, 5]),
    }
    dummy = hydrological_model(model_config)
    ds_out = dummy.get_streamflow()
    np.testing.assert_array_equal(ds_out["streamflow"].values[3], 3500.00)
    assert dummy.qsim.equals(ds_out)
    assert dummy.get_streamflow().equals(ds_out)
