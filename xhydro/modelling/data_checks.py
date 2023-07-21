import xclim as xc
import xclim.core.dataflags
import xarray as xr

import warnings


def health_checks(ds,
                 *,
                 structure: dict = None,
                 calendar: str = None,
                 variables_and_units: dict = None,
                 missing: str = None,
                 flags: dict = None,
                 raise_flags: bool = True):

    # Check the dimensions and coordinates
    if structure is not None:
        for dim in structure["dims"]:
            if dim not in ds.dims:
                raise ValueError(f"The dimension {dim} is missing.")
        for coord in structure["coords"]:
            if coord not in ds.coords:
                if coord in ds.data_vars:
                    warnings.warn(f"The variable {coord} is detected as a data variable, not a coordinate.", UserWarning, stacklevel=1)
                else:
                    raise ValueError(f"The coordinate {coord} is missing.")

    # Check the calendar
    if calendar is not None:
        trans = {
            "proleptic_gregorian": "standard",
            "gregorian": "standard",
            "default": "standard",
            "366_day": "all_leap",
            "365_day": "noleap",
            "julian": "standard",
        }
        cal = xc.core.calendar.get_calendar(ds.time)
        if not any(c in [cal, trans[cal]] for c in [calendar, trans[calendar] if calendar in trans else None]):
            raise ValueError(f"The calendar is not {calendar}.")

    # Check variables
    if variables_and_units is not None:
        for v in variables_and_units:
            if v not in ds:
                raise ValueError(f"The variable {v} is missing.")
            xc.core.units.check_units(ds[v], variables_and_units[v])

    # Quick check for irregular time steps
    freq = xr.infer_freq(ds.time)
    if freq is None:
        raise ValueError("The timesteps are irregular and cannot be inferred.")

    if missing is not None:
        if freq not in ["Y", "YS", "M", "MS", "H"]:
            warnings.warn(f"The frequency {freq} is not supported for missing data checks. That check will be skipped.", UserWarning, stacklevel=1)
        else:
            if isinstance(missing, str):
                missing = {missing: {}}
            if len(missing) > 1:
                raise NotImplementedError("Only one missing check can be performed at a time.")
            method = list(missing.keys())[0]
            if "freq" not in missing[method]:
                missing[method]["freq"] = "YS"
            for v in ds.data_vars:
                if missing == "any":
                    ms = xc.core.missing.missing_any(ds[v], **missing["any"])
                elif missing == "at_least_n_valid":
                    ms = xc.core.missing.at_least_n_valid(ds[v], **missing["at_least_n_valid"])
                elif missing == "missing_pct":
                    ms = xc.core.missing.missing_pct(ds[v], **missing["missing_pct"])
                elif missing == "wmo":
                    ms = xc.core.missing.missing_wmo(ds[v], **missing["wmo"])
                else:
                    raise ValueError(f"Missing check {missing} is not implemented.")
                if ms.any():
                    warnings.warn(f"The variable '{v}' has missing values.", UserWarning, stacklevel=1)

    if flags is not None:
        for v in ds.data_vars:
            if v in flags:
                xclim.core.dataflags.data_flags(ds[v], ds, flags=flags[v], raise_flags=raise_flags)
