from pathlib import Path

import numpy as np
import pytest
import xarray as xr
from xclim.testing.helpers import test_timeseries as timeseries

import xhydro as xh
import xhydro.testing.utils as xhu


class TestFakeHydrotelProject:
    def test_defaults(self, tmp_path):
        xhu.fake_hydrotel_project(tmp_path, "fake")
        assert (tmp_path / "fake").exists()
        assert (tmp_path / "fake" / "SLNO.csv").exists()
        assert (
            tmp_path / "fake" / "simulation" / "simulation" / "simulation.csv"
        ).exists()
        assert (tmp_path / "fake" / "simulation" / "simulation" / "output.csv").exists()

    def test_files(self, tmp_path):
        xhu.fake_hydrotel_project(
            tmp_path,
            "fake",
            meteo=True,
            debit_aval=True,
        )
        # Open the files to check if they are valid
        ds_meteo = xr.open_dataset(tmp_path / "fake" / "meteo" / "SLNO_meteo_GC3H.nc")
        assert ds_meteo.time.size == 730
        ds_debit_aval = xr.open_dataset(
            tmp_path
            / "fake"
            / "simulation"
            / "simulation"
            / "resultat"
            / "debit_aval.nc"
        )
        assert ds_debit_aval.time.size == 730

    def test_custom(self, tmp_path):
        meteo = timeseries(
            np.zeros(365 * 3),
            start="2001-01-01",
            freq="D",
            variable="tasmin",
            as_dataset=True,
            units="degC",
        )
        xhu.fake_hydrotel_project(
            tmp_path,
            "fake",
            meteo=meteo,
        )
        # Open the files to check if they are valid
        ds_meteo = xr.open_dataset(tmp_path / "fake" / "meteo" / "SLNO_meteo_GC3H.nc")
        assert ds_meteo.time.size == 1095
        np.testing.assert_array_equal(ds_meteo.data_vars, ["tasmin"])


@pytest.mark.requires_docs
def test_publish_release_notes(tmp_path):
    temp_md_filename = tmp_path.joinpath("version_info.md")
    xhu.publish_release_notes(
        style="md",
        file=temp_md_filename,
        changes=Path(__file__).parent.parent.joinpath("CHANGES.rst"),
    )

    with open(temp_md_filename) as f:
        changelog = f.read()

    assert changelog.startswith("# Changelog")
    version = xh.__version__
    vsplit = version.split(".")

    v_4history = (
        vsplit[0]
        + "."
        + str(int(vsplit[1]) + 1 if vsplit[2] != "0" else vsplit[1])
        + ".0"
    )
    assert f"## v{v_4history}" in changelog
    assert ":user:`" not in changelog
    assert ":issue:`" not in changelog
    assert ":pull:`" not in changelog

    temp_rst_filename = tmp_path.joinpath("version_info.rst")
    xhu.publish_release_notes(
        style="rst",
        file=temp_rst_filename,
        changes=Path(__file__).parent.parent.joinpath("CHANGES.rst"),
    )
    with open(temp_rst_filename) as f:
        changelog_rst = f.read()
    assert changelog_rst.startswith("=========\nChangelog\n=========")
