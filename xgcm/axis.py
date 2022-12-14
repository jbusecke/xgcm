from typing import Mapping, Tuple

import xarray as xr

from .padding import _XGCM_BOUNDARY_KWARG_TO_XARRAY_PAD_KWARG

VALID_POSITION_NAMES = "center|left|right|inner|outer"
FALLBACK_SHIFTS = {
    "center": ("left", "right", "outer", "inner"),
    "left": ("center",),
    "right": ("center",),
    "outer": ("center",),
    "inner": ("center",),
}


class Axis:
    _name: str
    _coords: Mapping[
        str, str
    ]  # TODO give this mapping from positions to dimension names a better name?
    _default_shifts: Mapping[str, str]
    _boundary: str
    _fill_value: float

    """A single direction along a model grid, containing potentially multiple cell positions."""

    def __init__(
        self,
        name: str,
        ds: xr.Dataset,
        coords: Mapping[str, str],  # TODO rename to dims
        default_shifts: Mapping[
            str, str
        ] = None,  # TODO type hint as Literal of the allowed options
        boundary: str = None,  # TODO type hint as Literal of the allowed options
        fill_value: float = None,
    ):
        """
        Create a new Axis object from an input dataset.

        Parameters
        ----------
        name : str
            Name of this Axis.
        ds : xarray.Dataset
            Contains the relevant grid information.
        coords : dict
            Mapping of axis positions to coordinate names
            (e.g. `{'center': 'XC', 'left: 'XG'}`)
        default_shifts : dict, optional
            Default mapping from and to grid positions
            (e.g. `{'center': 'left'}`). Will be inferred if not specified.
        boundary : str or dict
            boundary can either be one of {None, 'fill', 'extend', 'extrapolate', 'periodic'}
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Dirichlet boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Neumann boundary condition where
              the difference at the boundary will be zero.)
            * 'periodic' : Wrap arrays around. Equivalent to setting `periodic=True`
            This sets the default value. It can be overriden by specifying the
            boundary kwarg when calling specific methods.
        fill_value : float, optional
            The value to use in the boundary condition when boundary='fill'.
        """

        self._name = name

        # check all inputted values are valid here

        for pos, dim in coords.items():
            if pos not in VALID_POSITION_NAMES.split("|"):
                raise ValueError(
                    f"Axis position must be one of {VALID_POSITION_NAMES.split('|')}, but got {pos}"
                )
            if dim not in ds.dims:
                raise ValueError(
                    f"Could not find dimension `{dim}` (for the `{pos}` position on axis `{name}`) in input dataset."
                )
        self._coords = coords

        # set default position shifts

        _default_shifts = {}
        if default_shifts is None:
            default_shifts = {}
        for pos in self.coords:
            # use user-specified value if present

            if pos in default_shifts:
                _default_shifts[pos] = default_shifts[pos]
            else:
                for possible_shift in FALLBACK_SHIFTS[pos]:
                    if possible_shift in self.coords:
                        _default_shifts[pos] = possible_shift
                        break

            if pos in _default_shifts and _default_shifts[pos] == pos:
                # TODO stricter checking? e.g. non-adjacent positions?
                raise ValueError(
                    f"Can't set the default shift for {pos} to be to {pos}"
                )

        self._default_shifts = _default_shifts

        if boundary is None:
            boundary = "periodic"
        if boundary not in _XGCM_BOUNDARY_KWARG_TO_XARRAY_PAD_KWARG:
            raise ValueError(
                f"boundary must be one of {_XGCM_BOUNDARY_KWARG_TO_XARRAY_PAD_KWARG.keys()}, but got {boundary}"
            )
        self._boundary = boundary

        if fill_value is None:
            fill_value = 0.0
        if not isinstance(fill_value, (int, float)):
            raise TypeError("fill value must be an integer or a float")
        self._fill_value = fill_value

        # TODO backwards compatible attributes, to be removed --------------------

        if self._boundary == "periodic":
            self._periodic = True
        else:
            self._periodic = None

    @property
    def periodic(self) -> bool:
        return self._periodic

    # TODO end of backwards compatible section ------------------------------------

    @property
    def fill_value(self) -> float:
        return self._fill_value

    @property
    def name(self) -> str:
        return self._name

    @property
    def coords(self) -> Mapping[str, str]:
        return self._coords

    @property
    def default_shifts(self) -> Mapping[str, str]:
        return self._default_shifts

    @property
    def boundary(self) -> str:
        return self._boundary


    def _get_position_name(self, da: xr.DataArray) -> Tuple[str, str]:
        """Return the position and name of the axis coordinate in a DataArray."""

        axis_dims = self.coords.values()

        candidates = set(da.dims).intersection(set(axis_dims))

        if len(candidates) == 0:
            raise KeyError(
                f"None of the DataArray's dims {da.dims} were found in axis " "coords."
            )
        elif len(candidates) > 1:
            raise KeyError(
                f"DataArray cannot have more than 1 axis dimension, but found {candidates}"
            )
        else:
            for axis_position, axis_dim in self.coords.items():
                if axis_dim in da.dims:
                    return axis_position, axis_dim
            raise

    def _get_axis_dim_num(self, da: xr.DataArray):
        """Return the dimension number of the axis coordinate in a DataArray."""
        _, coord_name = self._get_position_name(da)
        return da.get_axis_num(coord_name)

    # TODO repr

    # TODO equals method

    def _assert_axes_equal(ax1, ax2):
        assert ax1.name == ax2.name
        for pos, coord in ax1.coords.items():
            assert pos in ax2.coords
            assert coord == ax2.coords[pos]
        assert ax1._periodic == ax2._periodic
        assert ax1._default_shifts == ax2._default_shifts
        assert ax1._facedim == ax2._facedim
        # TODO: make this work...
        # assert ax1._connections == ax2._connections
