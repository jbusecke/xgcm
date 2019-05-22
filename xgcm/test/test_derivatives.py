from __future__ import print_function
import xarray as xr

from xgcm.grid import Grid, Axis


def test_derivative_uniform_grid():
    # this is a uniform grid
    # a non-uniform grid would provide a more rigorous test
    dx = 10.0
    ds = xr.Dataset(
        {"foo": (("XC",), [1.0, 2.0, 4.0, 3.0])},
        coords={
            "XC": (("XC",), [0.5, 1.5, 2.5, 3.5]),
            "XG": (("XG",), [0, 1.0, 2.0, 3.0]),
            "dXC": (("XC",), [dx, dx, dx, dx]),
            "dXG": (("XG",), [dx, dx, dx, dx]),
        },
    )

    grid = Grid(
        ds,
        coords={"X": {"center": "XC", "left": "XG"}},
        metrics={("X",): ["dXC", "dXG"]},
        periodic=True,
    )

    dfoo_dx = grid.derivative(ds.foo, "X")
    expected = grid.diff(ds.foo, "X") / dx
    assert dfoo_dx.equals(expected)
