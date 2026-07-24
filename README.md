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

    This installs the core package, which has no obspy dependency. If you want to use the obspy-backed waveform sources for cross-correlation (see below), install the `obspy` extra instead:

    ```
    pip install -v ".[obspy]"
    ```

From now on you can activate the pyrtdd environment with:

    ```
    source .venv/bin/activate
    ```

You can disable it with:

    ```
    deactivate
    ```

If you want to run the test suite, install with the `test` and `obspy` extras and run pytest from the repo root: `pip install -v ".[test,obspy]"` then `pytest`.

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
        SolverOptions,
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
#    Ownership of `ttt` transfers into `dd` here (matching the C++
#    `unique_ptr` semantics), so it can't be reused afterwards. No waveform
#    proxy is passed, so this uses a `NoWaveformProxy()` internally and
#    cross-correlation stays off (see below for how to enable it).
cfg = Config() # see details later
dd = DD(cat, cfg, ttt)

# 4. Group events into clusters, then relocate them.
#    How multi-event relocation works: https://docs.gempa.de/scrtdd/current/base/multievent.html#relocation-process
cluster_cfg = ClusteringOptions() # see details later
clusters = dd.findClusters(cluster_cfg)

solver_cfg = SolverOptions()  # see details later
cat_new = dd.relocateMultiEvents(
    clusters, solver_cfg,
    saveProcessing=True, processingDataDir="")

# 5. Save the relocated catalog.
#    How to evaluate the results: https://docs.gempa.de/scrtdd/current/base/multievent.html#evaluating-the-results
cat_new.writeToFile('relocated-event.csv',
                    'relocated-phase.csv',
                    'relocated-station.csv')
```

![reloc](https://user-images.githubusercontent.com/15273575/205635799-80128f78-be04-48dc-8c17-32887d929552.png)

That's the whole shape of it (for the no-cross-correlation case), and it won't change. Everything below is just about *what you put into* the three config objects created above — `Config`, `ClusteringOptions`, and `SolverOptions` — before handing them to `DD`/`findClusters`/`relocateMultiEvents`.

Both `relocateMultiEvents` and `relocateSingleEvent` also accept two extra keyword arguments for debugging: `saveProcessing=True` dumps intermediate per-cluster/per-iteration data (input catalog, event/phase CSVs, the cross-correlation cache) to `processingDataDir`, at the cost of extra disk I/O; if `processingDataDir` is left empty (the default), a directory name is auto-generated in the current working directory.

## Configuration

### Phase catalog (`Config`)

Controls which picks in the input catalog are actually used. Set these on `cfg` before step 3 in the workflow above (`DD` reads `Config` once, at construction time):

```python
cfg = Config()

# Defines a list of accepted P and S phases. Phases not in the list will be discarded from the catalog.
cfg.validPphases = ['Pg', 'P']
cfg.validSphases = ['Sg', 'S']

# Used only if solver_cfg.usePickUncertainties=True.
#
# Sorts picks into weight classes by their time uncertainty (secs). This
# list is the class boundaries: class N covers the interval between the
# (N-1)th and Nth value, and its weight is 1 / 2^(N-1) -- so a higher class
# (= higher uncertainty) means a lower weight.
#   E.g. with the boundaries below, a pick with 0.150s uncertainty falls
#   into class 4 (0.100-0.200s) and gets weight 1 / 2^3 = 0.125.
#
# A pick with no uncertainty value, or an uncertainty at/above the last
# boundary (0.400s here), gets the worst (last) class -- i.e. the lowest
# weight, not the highest.
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
#
# Controls how neighbouring events are chosen for a reference event.
#
# Simple mode (numEllipsoids = 0): plain nearest-neighbour -- picks the
# closest events within 'maxNeighbourDist', up to 'maxNumNeigh' of them.
#
# Ellipsoid mode (numEllipsoids > 0, the default): Waldhauser (2009)'s
# concentric-ellipsoids algorithm, for a more spatially even selection.
# 'numEllipsoids' concentric ellipsoidal layers (increasing in thickness
# outward) are built around the reference event, each split into its 8
# quadrants, and neighbours are picked round-robin across every
# ellipsoid/quadrant cell until 'maxNumNeigh' is reached.
cluster_cfg.numEllipsoids = 0
cluster_cfg.maxNeighbourDist = 5  # Km
```

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
solver_cfg.xcorrWeightScaler = 2.0  # scales the weight given to cross-correlation-derived observations, see below
```

## Velocity model (`Homogeneous` / `NLLGrid`)

There are two options available. `Homogeneous` (used in the workflow above) assumes constant P/S velocities. Alternatively, `NLLGrid` reads travel times from precomputed NonLinLoc grids:

```python
ttt = NLLGrid(
    gridPath='path/to/grid',    # directory containing the NonLinLoc grid files
    gridModel='iasp91',         # grid model base name -- the common filename prefix
                                 #  NonLinLoc gives its time/angle/mod files, e.g.
                                 #  'iasp91.P.mod.hdr', 'iasp91.P.<station>.time.hdr', ...
    maxSearchDistance=0.01,     # NonLinLoc computes one grid file per station. Each file's
                                 #  header stores that station's location in grid-relative
                                 #  coordinates; a queried station's lat/lon is then matched
                                 #  to its grid by nearest projected location, not by
                                 #  station name/code. This is the max distance [m] allowed
                                 #  for that match -- beyond it, the lookup fails for that
                                 #  station. Kept tiny by default, since it only needs to
                                 #  absorb the projection's rounding error, not stand in for
                                 #  a missing station's grid with a nearby one's
    swapBytes=False,            # byte-swap grid file contents (set True on endianness
                                 #  mismatch between the machine that wrote the grids and
                                 #  the one reading them)
    maxOpenFiles=512,           # max number of grid files kept open at once (performance)
    accessMethod='KeepOpen',    # how grid files are read: 'KeepOpen' (the default) reads
                                 #  values from disk on demand, keeping the file open in
                                 #  between -- low memory use.
                                 #  'LoadIntoMemory' loads every grid file into memory
                                 #  upfront, trading a higher initial load time and memory
                                 #  footprint for the fastest lookups afterwards.
                                 # 'MemoryMapping' memory-maps the files instead; usually
                                 # the fastest option, but depends on your system, so
                                 # test it first
)
```

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
    clusters, solver_cfg,
    saveProcessing=True, processingDataDir="")
```

## Cross-correlation

Cross-correlation needs two things: a `pyrtdd.hdd.Proxy` to supply waveform data, passed to `DD` as its fourth (`wf`) argument, and an `XcorrOptions` configuring cross-correlation itself, passed to `relocateMultiEvents`/`relocateSingleEvent`. Putting both into the workflow above, this is the fuller form of its steps 3-4:

```python
from pyrtdd.hdd import XCorrCache

dd = DD(cat, cfg, ttt, proxy)  # `proxy`: see "Waveform sources" below

clusters = dd.findClusters(cluster_cfg)
xcorr_data = XCorrCache()  # gets populated with the computed corr coefficients/lags
xcorr_cfg = XcorrOptions() # see "Configuration" below
cat_new = dd.relocateMultiEvents(
    clusters, xcorr_data, xcorr_cfg, solver_cfg,
    saveProcessing=True, processingDataDir="")
```

`proxy` and `xcorr_cfg` are covered in detail next.

`xcorr_data` can be reused in a later call to skip recomputing cross-correlation pairs it already has entries for — including across separate runs, by saving it to disk once and reloading it later:

```python
# Save (`cat` must be the same background catalog the cache was computed against).
xcorr_data.writeToFile(cat, "xcorr_cache.csv")

# Later, reload it instead of recomputing cross-correlation from scratch:
xcorr_data = XCorrCache.readFromFile(cat, "xcorr_cache.csv")
cat_new = dd.relocateMultiEvents(
    clusters, xcorr_data, xcorr_cfg, solver_cfg,
    saveProcessing=True, processingDataDir="")
```

Reusing a cache like this only pays off for pairs it already has entries for — any event/station/phase combination it doesn't cover still gets cross-correlated normally (and is added to `xcorr_data` as usual).


### Waveform sources (`pyrtdd.hdd.Proxy`)

`Proxy` is a Python-subclassable base class: any object whose class inherits from `hdd.Proxy` and implements its methods (`loadTrace`, `loadTraces`, `getComponentsInfo`, `filter`, `writeTrace`, `readTrace`) can be handed to `DD`, and `enableCatalogWaveformDiskCache`/preloading work against it automatically, regardless of where the data actually comes from.

`pyrtdd.obspy.waveform` (not imported by `pyrtdd`/`pyrtdd.hdd` — install with `pip install pyrtdd[obspy]` and import it explicitly) provides three ready-made obspy-backed implementations:

```python
from pyrtdd.obspy.waveform import StreamProxy, ObspyClientProxy, FileScannerProxy

# Wrap waveforms already loaded into an obspy.Stream.
proxy = StreamProxy(stream, inventory)

# Wrap any obspy client exposing get_waveforms(net, sta, loc, cha, t0, t1),
# e.g. obspy.clients.filesystem.sds.Client, obspy.clients.fdsn.Client, or
# obspy.clients.earthworm.Client. get_waveforms_bulk is used automatically
# for preloading/caching when the client supports it (e.g. FDSN).
proxy = ObspyClientProxy(client, inventory)

# Scan a local folder for waveform files (any format obspy can read, e.g.
# miniSEED) and serve them like an archive. The folder is indexed once, by
# reading file headers only, at construction time.
proxy = FileScannerProxy("/path/to/waveforms", inventory)
```

All three need an `obspy.Inventory` (StationXML) to resolve channel orientation (dip/azimuth) for the `R`/`T`/`L2` component transforms — `L2` is the default for S phases, so this is needed even for the default config. If a channel's orientation can't be resolved from the inventory, `guess_zne=True` falls back to assuming a standard Z/N/E layout (dip -90/0/0, azimuth 0/0/90); the default, `guess_zne=False`, raises instead of guessing.

Writing your own `Proxy` subclass (e.g. for a different data source, or a non-obspy pipeline) is the same shape as `pyrtdd.obspy.waveform`'s implementations — subclass `pyrtdd.hdd.Proxy` and implement its six methods.

### Configuration (`XcorrOptions`)

The full set of `XcorrOptions` fields behind the `xcorr_cfg` used in the template above (defaults shown):

```python
from pyrtdd.hdd import XcorrOptions

PhaseType = Catalog.Phase.Type

xcorr_cfg = XcorrOptions()
xcorr_cfg.enable = True

# Station filtering (this can be more restrictive than the clustering phase)
xcorr_cfg.minEvStaDist   = 0   # min event to station distance
xcorr_cfg.maxEvStaDist   = -1  # max event to station distance. -1 -> disable
xcorr_cfg.maxInterEvDist = -1  # max inter-event distance. -1 -> disable

# Per-phase-type settings (defaults shown)
xcorr_cfg.phase[PhaseType.P].minCoef     = 0.70  # min cross-correlation coefficient required (0-1)
xcorr_cfg.phase[PhaseType.P].startOffset = -0.50 # xcorr window start: secs before the pick
xcorr_cfg.phase[PhaseType.P].endOffset   = 0.50  # xcorr window end: secs after the pick
xcorr_cfg.phase[PhaseType.P].winScaling  = 0.02  # window scaling coefficient:
                                                  #  windowLength = (endOffset - startOffset) + travelTime * winScaling
xcorr_cfg.phase[PhaseType.P].maxDelay    = 0.50  # max allowed lag between the two traces being cross-correlated, secs
xcorr_cfg.phase[PhaseType.P].components  = ["Z"] # priority list of components to try, in order, until one succeeds
                                                  #  each entry is either a literal orientation code (e.g. "Z"), or one
                                                  #  of the computed transforms "R" (radial), "T" (transversal), "L2"
                                                  #  ("R"/"T"/"L2" need channel orientation info -- see "Waveform
                                                  #  sources" above)

xcorr_cfg.phase[PhaseType.S].minCoef     = 0.70
xcorr_cfg.phase[PhaseType.S].startOffset = -0.50
xcorr_cfg.phase[PhaseType.S].endOffset   = 1.00
xcorr_cfg.phase[PhaseType.S].winScaling  = 0.04
xcorr_cfg.phase[PhaseType.S].maxDelay    = 0.50
xcorr_cfg.phase[PhaseType.S].components  = ["L2"]
```

`relocateMultiEvents`/`relocateSingleEvent` also take the `XCorrCache` argument (`xcorr_data` in the template above), used to cache computed coefficients/lags.

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

## Logging

`pyrtdd` logs progress (like the cluster/relocation messages seen when running the workflow above) to `stderr`. It defaults to the `info` level. You can change it at any time, e.g. before or between relocation calls:

```python
from pyrtdd.hdd import Logger

Logger.setLevel(Logger.Level.debug)  # more verbose
Logger.getLevel()                    # read back the current level
```

Available levels, from most to least verbose: `Logger.Level.debug`, `Logger.Level.info` (the default), `Logger.Level.warning`, `Logger.Level.error`, `Logger.Level.none` (disables logging entirely).
