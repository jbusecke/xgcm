Quickstart
=====================

What is xgcm for?
-----------------
.. raw:: html

    <div style="position: relative; padding-bottom: 10.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/lo6JvrJ-YA8" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>

What ingredients do I need to start with xgcm?
----------------------------------------------
1. An :ref:`installed <installation>` version of xgcm
2. Your xarray dataset of choice `ds`.
3. Information on how the grid of `ds` is layed out. This is often encoded in metadata, or else you need to infer it from the dataset (see more below).
4. (Optional) All "metrics" you have available in the dataset (think: cell distances, areas, volumes). You need these if you want to use the higher-level derivative and integral functions.


How to get started - Step by step
---------------------------------
The `Grid` object is essential to the way xgcm works. It stores information about the grid setup for you. 
`Grid` knows about the logical [axes], which dimensions and metrics (represented by xarray `coordinates <http://xarray.pydata.org/en/stable/data-structures.html#coordinates>`_) belong to each axis.
All this information will only have to be set once and then you can focus on whatever task is at hand without needing to remember the details.
This becomes especially handy when you try to compute things on multiple datasets with different grid setups. 

.. note::
    It is necessary to create a unique 'Grid' object for each dataset with a different grid!

1. Check what xgcm can figure out by itself. 
    xgcm can parse :ref:`certain metadata conventions <axis_detection>` 
    and a good starting point is usually to see if xgcm can automatically detect some information about your grid.

    .. code-block:: python

        from xgcm import Grid
        grid = Grid(ds)
        print(grid)

    What output do you get from this?

    If you see

    .. code-block:: python

        <xgcm.Grid>

    and nothing else, xgcm did not find any metadata to identify any `axis`. You need to manually specify the axes (shown below).

    If you see anything else, you are in luck and xgcm detected axes from the metadata. If all your desired axes are present, you can skip the next step.
2. Investigate the dataset, and determine which :ref:`axis position <axis_position>` is represented by the dimensions of `ds`.
    Lets take the `CESM MOM6 Ocean Model Example Data <https://catalog.pangeo.io/browse/master/ocean/cesm_mom6_example/>`_ to go through the steps:
    
    .. figure:: images/quickstart_example.png
        :scale: 75 %
        :alt: CESM Example workflow

    a. For many earth science datasets the convention is to call the position of tracers (temperature, salinity, etc.) `center`. 
    Find a tracer data variable (we take `SSH`; the sea surface height). Note the dimensions: `(time, yh, xh)`. 
    Lets focus on one of them for now: `xh`.
    We have to choose an axis name. `X` seems like a good choice. We can start building our dictionary: `{'center':'xh'}`.

    b. Now we need to find other possible dimensions that are on the same axis. Look for data variables that have other dimensions, like e.g. velocities. Here we could
    take `u` with the dimensions `(time, z_l, yh, xq)`. We can infer that `xq` belongs on the same axis as `xh`.

    c. Where is `xh` located relative to `xq` though? If you have no additional information, you can try to compare the values of the dimensions. In
    this case we see that `xh` and `xq` have the same number of values and for each value `xq>xh`, we can thus infer that `xh` is on the `left` position. 
    The full dictionary for the axis would be `{'center':'xq','left':'xh'}`.

    d. Repeat the steps above for each desired axis and pass a nested dictionary to the `Grid` object. E.g. ``Grid(coords={
    'X':{'center':'xq','left':'xh'}, 'Y':{...}, 'Z':{...}})``

    Find more detailed instructions :ref:`here <grids>`.

    If you have only one dimension per axis, the default is to put it at the `center` location. This works but most of the functionality of xgcm does require 
    two grid positions. You can find instructions on how to reconstruct additional dimensions `here <autogenerate_examples.ipynb>`_.
3. Determine if your axes are periodic or define a boundary condition.
    You can specify this either for all axes ``Grid(ds, periodic=False, boundary='fill')``
    or per axis, by passing a list/dictionary with separate axis names ``Grid(ds, periodic=['X'], boundary={'Y':'fill'}``.
    The boundary condition is used for operations at the boundary points (of the array, not physical boundaries like continents), when an extra point needs to be added.
4. Parse the `metrics <grid_metrics.ipynb>`_.
    For this you should find out all the variables in your dataset that represent a metric (distance, area, volume),
    and sort them according to the axis or axes they represent. You can then pass a dictionary with a tuple of the representative axis/axes as key
    and the names of the corresponding fields in `ds` as a list of strings. xgcm will automatically figure out to which grid position they belong. 
    An example for two distances along the `X` axis and two areas in the `X`/`Y` plane: ``{('X'):['distance_a', 'distance_b'], ..., ('X', 'Y'):['area_i', 'area_j'],}``. 
    This dictionary can contain any combination of axes as keys. The more metrics you have, the more accurate the results will be. 

Finally put all those steps together:

.. code-block:: python

    grid = Grid(ds, 
                coords = {...},  #From step 2
                periodic = [], #From step 3
                boundary = [], #From step 3
                metrics = {...}, # From step 4
                )

Explanation of the grid object output
-------------------------------------

You can get information about the grid by printing it:

.. code-block:: python

    print(grid)

You should get a result looking similar to:

.. code-block:: python

    <xgcm.Grid>
    X Axis (periodic, boundary=None):
      * center   xq --> left
      * left     xh --> center
    Z Axis (not periodic, boundary='extend'):
      * center   z_center --> right
      * right    z_face   --> center

First, we see the list of all axes detected, here ``X`` and ``Z``.

Followed in the parenthesis, are the default periodic and boundary conditions for each axis.
Please mind that the following version of xgcm will refactor these names.

Then for each axis the positions are shown. Here the ``X`` axis has 2 positions,
``center`` and ``left``, and the ``Z`` axis also has 2 positions, ``center`` and ``right``.
5 positions are available in xgcm, ``center``, ``left``, ``right``, ``inner`` and ``outer``,
:ref:`see the positions doc <axis_position>`

Following the position, is the name of the dataset dimension, e.g.
``xq`` is the name of the dimension of the ``center`` position of the ``X`` axis,
and ``xh``the name of the dimension of the ``left``  position of the ``X`` axis.

The arrow ``-->`` indicates the default shift (used for grid operations).
It is possible to use xgcm without understanding the shifts, as the grid object
handles these shifts.


What do the metrics represent?
------------------------------

Simple periodic case
....................

Let's define a simple grid with a single periodic axis, with a left point (face)
``F`` and a center point ``C``, the numbers represent the index.
Please note that the last F and C points are equal to the 1st ones (due to periodicity).
From this grid we define 2 types of metrics, that represent the distance between the faces (F)
and the center (C) points. Thus the distance between the faces defines the metric associated
with the C point (we call it ``dxC``), and the distance between the center points
defines the metric associated with the F point (called here ``dxF``).

::



    |             |             |             |             |
    F------C------F------C------F------C------F------C------F------C
    0      0      1      1      2      2      3      3      0      0
    |             |             |             |             |
    |<----dxC---->|<----dxC---->|<----dxC---->|<----dxC---->|
    |             |             |             |             |
           |<----dxF---->|<----dxF---->|<----dxF---->|<----dxF---->|



You can see that each metric is linked to each point (the point ``C[0]`` has the metric
``dxC[0]``, the point ``F[1]`` has the metric ``dxF[1]``, etc). In simple case the distances
can be identical and thus only scalar
(in the case of perfectly squared grid cells), in more complex cases
they can vary with e.g. longitude, latitude, depth, or time. What matters is that the
metric dimensions can be broadcasted against the dimensions of variables living at the
same position (e.g. temperature at the cell center).

In this simple periodic case, the grid / array boundaries are simple to deal with
(extend the array). The next section gives some keys on how to deal with closed boundaries.


Not periodic case
.................

Let's take the same grid as previously, but non periodic:

::



    |             |             |             |
    F------C------F------C------F------C------F------C
    0      0      1      1      2      2      3      3
    |             |             |             |
    |<----dxC---->|<----dxC---->|<----dxC---->|
    |             |             |             |
           |<----dxF---->|<----dxF---->|<----dxF---->|

    
We hit here a problem: the first F point ``F[0]`` and the last C point ``C[3]``
are not surrounded by respectively 2 C points or 2 F points. In the easy case where these
point are located inside the bathymetry or land (e.g. if one defines a square grid of
the northern Atlantic Ocean, the eastern and western boundaries will probably
be located in Europe and America), any number can fit for the metric, as it will
not be used in any physical calculation. Note that a metric needs to exists in this point,
it is not possible to have a shorter array!
In more complex cases, the choice of the value for ``dxF[0]`` and ``dxC[3]`` is left to
the user. A common choice is represented below (we only show here for the ``dxF`` metric,
but it is similar for the ``dxC`` one).


::



    |             |             |             |
    F------C------F------C------F------C------F------C
    0      0      1      1      2      2      3      3
    |             |             |             |
    |<dxF->|<----dxF---->|<----dxF---->|<----dxF---->|


Making this choice we only take the distance between ``F[0]`` and ``C[0]``.
