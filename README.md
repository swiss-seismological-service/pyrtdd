[![DOI](https://zenodo.org/badge/246001157.svg)](https://zenodo.org/badge/latestdoi/246001157)

Please cite the code as:

"Luca Scarabello & Tobias Diehl (2021). swiss-seismological-service/scrtdd. Zenodo doi: 10.5281/zenodo.5337361"

# pyrtdd

Python wrapper for the C++ double-difference relocation library from [scrtdd](https://github.com/swiss-seismological-service/scrtdd). `pyrtdd` currently tracks scrtdd [v2.0.8](https://github.com/swiss-seismological-service/scrtdd/releases/tag/v2.0.8).


# Installation

1. Clone this repository, ensuring that `scrtdd` is also pulled as a submodule:

    ```
    git clone --recursive https://github.com/swiss-seismological-service/pyrtdd.git
    ```

2. Create a virtual environment where you will install pyrtdd:

    ```
    python3 -m venv .venv
    ```

3. Activate the virtual environment:

    ```
    source .venv/bin/activate
    ```

4. Install `pyrtdd` from source:

    ```
    pip install -v .
    ```

From now on you can activate the pyrtdd environment with:

    ```
    source .venv/bin/activate
    ```

You can disable it with:

    ```
    deactivate
    ```

# Example workflow

Please note that this is a simple python wrapper, but the official documentation is only available for the SeisComP module [scrtdd](https://github.com/swiss-seismological-service/scrtdd).

Running a relocation is always the same five steps: load a catalog, pick a velocity model, build the relocator, cluster + relocate, save the result. This runs as-is against the test data in this repo:

```python
from pyrtdd.hdd import (
        Catalog,
        Config,
        Homogeneous,
        DD,
        ClusteringOptions,
        XcorrOptions,
        SolverOptions,
        XCorrCache,
        NoWaveformProxy,
    )

# 1. Load the input catalog: stations, events, and phase picks.
#    Here we use the test catalog included in this repo.
#    Catalog format: https://docs.gempa.de/scrtdd/current/base/multievent.html#event-catalog-plain-csv-files
cat = Catalog('./package/test/py/data/starting-station.csv',
              './package/test/py/data/starting-event.csv',
              './package/test/py/data/starting-phase.csv')

# 2. Pick a velocity model. See below for other models
ttt = Homogeneous(5.8, 3.36)  # P/S velocity [km/s]

# 3. Build the relocator.
#    Ownership of `ttt`/`wf` transfers into `dd` here (matching the C++
#    `unique_ptr` semantics), so neither can be reused afterwards.
cfg = Config() # see details later
dd = DD(cat, cfg, ttt, NoWaveformProxy())

# 4. Group events into clusters, then relocate them.
#    How multi-event relocation works: https://docs.gempa.de/scrtdd/current/base/multievent.html#relocation-process
cluster_cfg = ClusteringOptions() # see details later
clusters = dd.findClusters(cluster_cfg)

solver_cfg = SolverOptions()  # see details later
cat_new = dd.relocateMultiEvents(
    clusters, XCorrCache(), cluster_cfg, XcorrOptions(), solver_cfg,
    saveProcessing=True, processingDataDir="")

# 5. Save the relocated catalog.
#    How to evaluate the results: https://docs.gempa.de/scrtdd/current/base/multievent.html#evaluating-the-results
cat_new.writeToFile('relocated-event.csv',
                    'relocated-phase.csv',
                    'relocated-station.csv')
```

![reloc](https://user-images.githubusercontent.com/15273575/205635799-80128f78-be04-48dc-8c17-32887d929552.png)

That's the whole shape of it, and it won't change. Everything below is just about *what you put into* the four config objects created above — `Config`, `ClusteringOptions`, `XcorrOptions`, and `SolverOptions` — before handing them to `DD`/`findClusters`/`relocateMultiEvents`.

Both `relocateMultiEvents` and `relocateSingleEvent` also accept two extra keyword arguments for debugging: `saveProcessing=True` dumps intermediate per-cluster/per-iteration data (input catalog, event/phase CSVs, the cross-correlation cache) to `processingDataDir`, at the cost of extra disk I/O; if `processingDataDir` is left empty (the default), a directory name is auto-generated in the current working directory.

## Configuration

### Phase catalog (`Config`)

Controls which picks in the input catalog are actually used. Set these on `cfg` before step 3 in the workflow above (`DD` reads `Config` once, at construction time):

```python
# Defines a priority list of accepted P and S phases. Phases not in the list will be discarded from the catalog.
# If multiple phases exist for the same event at a station, the first one in the list will be used
cfg.validPphases = ['Pg', 'P']
cfg.validSphases = ['Sg', 'S']

# Defines pick time uncertainty thresholds (in seconds) used to classify
# picks for weighting. This parameter defines a list of interval boundaries.
# A pick's class is determined by the interval its uncertainty falls into.
# E.g., a pick with an uncertainty of 0.150s falls into the 4th interval
# (between 0.100 and 0.200) and is assigned class 4. If a pick's
# uncertainty is absent, the lowest class is used.
# The pick weight is computed as: 1 / 2^(class-1).
# Used only if solver_cfg.usePickUncertainties=True
cfg.pickUncertaintyClasses = [0.000, 0.025, 0.050, 0.100, 0.200, 0.400]
```

### Clustering (`ClusteringOptions`)

These options control which events and phases are used in the double-difference equation system.

```python
cluster_cfg = ClusteringOptions()

# Quality settings: allow to drop poorly connected events or bad phases
cluster_cfg.minNumNeigh = 8  # min neighbors required for an event
cluster_cfg.minNumPhases = 8  # min differential times per event pair required (i.e. how many P+S phases)

# Performance settings:
#  limit maxNumPhases only if the relocation is too slow, otherwise keep them all
#  maxNumNeigh doesn't usually improve results above 30-40
cluster_cfg.maxNumNeigh = 40  # max neighbors allowed. 0 -> disable
cluster_cfg.maxNumPhases = 0  # max differential times per event pair required (Including P+S) 0 -> disable

# Station filtering
cluster_cfg.minEvStaToInterEvRatio = 0.  # min hypocenter-station to interevent distance ratio required
cluster_cfg.minEvStaDist = 0.  # min hypocenter-station distance required
cluster_cfg.maxEvStaDist = -1  # max hypocenter-station distance allowed (-1 -> disable)

# Neighbours selection
# This option controls how neighbouring events are selected. When 'numEllipsoids' is > 0 (the default),
# the ellipsoid selection algorithm from Waldhauser 2009 is used: to assure a spatially homogeneous
# subsampling, reference events are selected within each of `numEllipsoids` concentric ellipsoidal
# layers of increasing thickness. Each layer is split up into its 8 quadrants (or cells), and the
# neighboring events are selected from each ellipsoid/quadrant combination in a round robin fashion
# until 'maxNumNeigh' is reached.
# In the simplest form, 'numEllipsoids' is set to 0 and 'maxNumNeigh' neighbours are instead selected
# on a plain nearest-neighbour basis within a search distance of 'maxNeighbourDist'.
cluster_cfg.numEllipsoids = 0
cluster_cfg.maxNeighbourDist = 5  # Km
```

### Cross-correlation (`XcorrOptions`)

There is no cross-correlation binding to python yet, so leave this disabled :(

```python
xcorr_cfg = XcorrOptions()
xcorr_cfg.enable = False
```

Relatedly, `relocateMultiEvents`/`relocateSingleEvent` also take an `XCorrCache` argument — a cache of precomputed cross-correlation results for the phases being relocated. Since cross-correlation isn't implemented in pyrtdd, always pass an empty `XCorrCache()` there.

### Solver (`SolverOptions`)

Double-difference equations system solver configuration.

```python
solver_cfg = SolverOptions()

solver_cfg.type = "LSMR"  # Solver algorithm to use: either LSMR or LSQR
solver_cfg.algoIterations = 20  # how many iterations the solver performs

solver_cfg.absLocConstraintStart = 0.3  # 0 -> disable absolute location constraint
solver_cfg.absLocConstraintEnd = 0.3    # 0 -> disable absolute location constraint
solver_cfg.dampingFactorStart = 0.01    # 0 -> disable damping factor
solver_cfg.dampingFactorEnd = 0.01      # 0 -> disable damping factor

solver_cfg.downWeightingByResidualStart = 10.  # 0 -> disbale downweighting
solver_cfg.downWeightingByResidualEnd = 5.     # 0 -> disbale downweighting

solver_cfg.usePickUncertainties = False  # if True then phase uncertaintis must
                                         #  be populated in cfg.pickUncertaintyClasses
solver_cfg.xcorrWeightScaler = 2.0  # scales the weight given to cross-correlation-derived observations
```

## Velocity model (`Homogeneous` / `NLLGrid`)

There are two options available. `Homogeneous` (used in the workflow above) assumes constant P/S velocities. Alternatively, `NLLGrid` reads travel times from precomputed NonLinLoc grids:

```python
ttt = NLLGrid('path/to/grid',   # directory containing the NonLinLoc grid files
              'iasp91',         # grid model name
              0.1,              # max search distance [km] used to match a station to a grid node
              False,            # swap bytes
              512,              # maximum number of grid files to keep open (performance)
              'MemoryMapping')       # grid file access method
```

The method for accessing grid files can be 'KeepOpen', 'LoadIntoMemory' or 'MemoryMapping'
'MemoryMapping' is the fastest method, but it is optional in case there are limits of
memoery mapping on your system.
'KeepOpen' opens the files and reads the required values on demand, while keeping the file open.
'LoadIntoMemory' loads all files into memory. This requires an initial file loading overhead
and higher memory usage. This is the fastest method for long running modules that
can keep all the grid files in memory, so that they are loaded only once.

Both `Homogeneous` and `NLLGrid` also work standalone, if you need travel times for your own
purposes rather than for a relocation:

```python
# Travel time only [seconds], given an event location and a station location.
travelTime = ttt.compute(
    eventLat, eventLon, eventDepth,      # event location [degrees, degrees, km]
    stationLat, stationLon, stationElevation,  # station location [degrees, degrees, meters]
    'P')  # phase type

# Travel time plus the takeoff angles and slowness, as a tuple:
# (travelTime [sec], takeOffAzimuth [degrees], takeOffDip [degrees, 0=down:180=up],
#  dtdd [angular slowness, sec/degree], dtdh [vertical slowness, sec/km])
travelTime, takeOffAzimuth, takeOffDip, dtdd, dtdh = ttt.computeAll(
    eventLat, eventLon, eventDepth, stationLat, stationLon, stationElevation, 'P')
```

## Saving and reloading clusters

`findClusters` can be slow on large catalogs, and `relocateMultiEvents` consumes its `clusters` argument (it can't be reused for a second run). If you want to experiment with different `xcorrOpt`/`solverOpt` settings without recomputing clusters every time, save them to disk once and reload them later:

```python
from pyrtdd.hdd import Neighbours

clusters = dd.findClusters(cluster_cfg)

# Save: one file per cluster (each cluster is a dict of {eventId: Neighbours}).
for i, cluster in enumerate(clusters):
    Neighbours.writeToFile(cluster, cat, f"cluster_{i}.csv")

# Later, reload them (`cat` must be the same catalog used to compute the clusters):
clusters = [Neighbours.readFromFile(cat, f"cluster_{i}.csv") for i in range(len(clusters))]

cat_new = dd.relocateMultiEvents(
    clusters, XCorrCache(), cluster_cfg, xcorr_cfg, solver_cfg)
```

## Logging

`pyrtdd` logs progress (like the cluster/relocation messages seen when running the workflow above) to `stderr`. It defaults to the `info` level. You can change it at any time, e.g. before or between relocation calls:

```python
from pyrtdd.hdd import Logger

Logger.setLevel(Logger.Level.debug)  # more verbose
Logger.getLevel()                    # read back the current level
```

Available levels, from most to least verbose: `Logger.Level.debug`, `Logger.Level.info` (the default), `Logger.Level.warning`, `Logger.Level.error`, `Logger.Level.none` (disables logging entirely).

## Relocating a single event

The workflow above (`findClusters` + `relocateMultiEvents`) relocates every event in the catalog against each other — this is the common case and the one you'll normally want. `DD` also supports relocating one event at a time against the background catalog already loaded into `dd`, e.g. for near-real-time relocation as new events come in one by one. It's a separate call, `relocateSingleEvent`, and isn't needed unless that's specifically what you're after:

```python
# The event to relocate, as its own one-event `Catalog` (station + phase picks
# included). Here we just pull an existing event out of `cat` as an example;
# normally this would be a newly detected event not yet in the background catalog.
single_event_cat = cat.extractEvent(event_id, True)  # True -> keep the same event id

# How single-event relocation works: https://docs.gempa.de/scrtdd/current/base/singleevent.html#relocation-process
reloc_cat = dd.relocateSingleEvent(
    single_event_cat,
    True,  # isManual: True if the picks are manually reviewed, False if automatic/preliminary
    cluster_cfg, xcorr_cfg, solver_cfg,
    saveProcessing=True, processingDataDir="")
```

`dd` finds neighbours for this one event from its background catalog the same way `findClusters` would, then relocates it against them. Note the relocated event gets a new event id in `reloc_cat` (it isn't guaranteed to match `event_id`).
