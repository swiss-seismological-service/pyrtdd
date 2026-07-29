"""pyrtdd relocation template -- WITHOUT cross-correlation.

Fills in the basic multi-event relocation workflow (catalog -> velocity
model -> cluster -> relocate -> save) with every option documented in the
README's "Configuration" / "Velocity model" sections, using their defaults.

Fields you must fill in yourself are marked "# TODO". Everything else is a
tunable default copied from the README -- read the corresponding README
section before changing it, since most of these interact with each other.

If you need cross-correlation, see relocate_with_xcorr.py instead. Loading the
catalog from obspy instead of CSV (step 1 below) also needs the obspy extra,
but is otherwise independent of cross-correlation.

Usage:
    python examples/relocate.py
"""

from pyrtdd.hdd import (
    Catalog,
    Config,
    Homogeneous,
    NLLGrid,
    ClusteringOptions,
    SolverOptions,
    DD,
    Logger,
)

# -----------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------

# debug, info (default), warning, error, or none (disables logging entirely)
Logger.setLevel(Logger.Level.info)

# -----------------------------------------------------------------------
# 1. Load the input catalog: stations, events, and phase picks.
#    Pick ONE of the two options below.
# -----------------------------------------------------------------------

# Option A: plain CSV files.
#    Format: https://docs.gempa.de/scrtdd/current/base/multievent.html#event-catalog-plain-csv-files
cat = Catalog(
    "<path/to/station.csv>",  # TODO
    "<path/to/event.csv>",  # TODO
    "<path/to/phase.csv>",  # TODO
)

# Option B: from an obspy Catalog + Inventory instead (comment out Option A
# above if using this). Requires the obspy extra: pip install -v ".[obspy]"
# import obspy
# from pyrtdd.obspy.catalog import catalog_from_obspy
#
# obspy_catalog = obspy.read_events("<path/to/catalog.xml>")  # TODO
# inventory = obspy.read_inventory("<path/to/inventory.xml>")  # TODO
# cat = catalog_from_obspy(obspy_catalog, inventory)
#
# Optional: dump the converted catalog, you can load this catalog the next time
#
# cat.writeToFile('input-station.csv', 'input-event.csv', 'input-phase.csv')

# -----------------------------------------------------------------------
# 2. Phase catalog configuration: controls which picks are actually used.
# -----------------------------------------------------------------------

cfg = Config()

# Accepted P and S phases. Phases not in these lists are discarded from the
# catalog. If multiple phases exist for the same event/station, the first
# one in the list wins.
cfg.validPphases = ["P", "Pg", "Pn"]
cfg.validSphases = ["S", "Sg", "Sn"]

# Used only if solver_cfg.usePickUncertainties=True (see below).
#
# Sorts picks into weight classes by their time uncertainty (secs). This
# list is the class boundaries: class N covers the interval between the
# (N-1)th and Nth value, and its weight is 1 / 2^(N-1). A higher class
# (meaning higher uncertainty) therefore gets a lower weight. A pick with
# no uncertainty value, or an uncertainty at/above the last boundary, gets
# the worst (last) class, meaning the lowest weight, not the highest.
cfg.pickUncertaintyClasses = [0.000, 0.025, 0.050, 0.100, 0.200, 0.400]

# -----------------------------------------------------------------------
# 3. Velocity model: pick ONE of the two options below.
# -----------------------------------------------------------------------

# Option A: constant P/S velocities.
ttt = Homogeneous(
    5.8,  # TODO: P velocity [km/s]
    3.36,  # TODO: S velocity [km/s]
)

# Option B: precomputed NonLinLoc grids (comment out Option A above if using this).
# ttt = NLLGrid(
#     gridPath="<path/to/grid>",  # TODO: directory containing the NonLinLoc grid files
#     gridModel="<model>",  # TODO: grid model base name (filename prefix), e.g. "iasp91"
#     maxSearchDistance=10.0,  # max distance [m] allowed between a queried station's
#                              #  location and the location recorded in a grid file's
#                              #  header (see README "Velocity model" for why this is tiny)
#     swapBytes=False,  # byte-swap grid file contents (set True on endianness mismatch
#                        #  between the machine that wrote the grids and this one)
#     maxOpenFiles=512,  # max number of grid files kept open at once (performance)
#     accessMethod="KeepOpen",  # 'KeepOpen' (default, low memory), 'LoadIntoMemory'
#                                #  (fastest lookups, higher upfront cost), or
#                                #  'MemoryMapping' (usually fastest, test it first)
# )

# -----------------------------------------------------------------------
# 4. Build the relocator.
#    No waveform proxy is passed, so cross-correlation stays off.
# -----------------------------------------------------------------------

dd = DD(cat, cfg, ttt)

# -----------------------------------------------------------------------
# 5. Clustering: controls which events/phases enter the double-difference
#    equation system, and how neighbouring events are selected.
# -----------------------------------------------------------------------

cluster_cfg = ClusteringOptions()

# Quality settings: allow dropping poorly connected events or bad phases
cluster_cfg.minNumNeigh = 8  # min neighbors required for an event
cluster_cfg.minNumPhases = 8  # min differential times per event pair required (P+S)

# Performance settings: limit maxNumPhases only if the relocation is too
# slow, otherwise keep them all. maxNumNeigh doesn't usually improve
# results above 30-40.
cluster_cfg.maxNumNeigh = 40  # max neighbors allowed. 0 -> disable
cluster_cfg.maxNumPhases = 0  # max differential times per event pair (P+S). 0 -> disable

# Station filtering
cluster_cfg.minEvStaToInterEvRatio = 3.0  # min hypocenter-station to interevent distance ratio
cluster_cfg.minEvStaDist = 0.0  # min hypocenter-station distance required
cluster_cfg.maxEvStaDist = -1  # max hypocenter-station distance allowed. -1 -> disable

# Neighbours selection. Simple mode (numEllipsoids = 0): plain nearest-
# neighbour, picking the closest events within maxNeighbourDist, up to
# maxNumNeigh of them. Ellipsoid mode (numEllipsoids > 0, the default):
# Waldhauser (2009)'s concentric-ellipsoids algorithm, for a more spatially
# even selection -- see README "Clustering" for the full explanation.
cluster_cfg.numEllipsoids = 0
cluster_cfg.maxNeighbourDist = 5  # Km

# -----------------------------------------------------------------------
# 6. Solver: double-difference equations system solver configuration.
# -----------------------------------------------------------------------

solver_cfg = SolverOptions()

solver_cfg.type = "LSMR"  # Solver algorithm to use: either LSMR or LSQR
solver_cfg.algoIterations = 20  # how many iterations the solver performs

solver_cfg.absLocConstraintStart = 0.3  # 0 -> disable absolute location constraint
solver_cfg.absLocConstraintEnd = 0.3  # 0 -> disable absolute location constraint
solver_cfg.dampingFactorStart = 0.01  # 0 -> disable damping factor
solver_cfg.dampingFactorEnd = 0.01  # 0 -> disable damping factor

solver_cfg.downWeightingByResidualStart = 10.0  # 0 -> disable downweighting
solver_cfg.downWeightingByResidualEnd = 5.0  # 0 -> disable downweighting

solver_cfg.usePickUncertainties = False  # if True, cfg.pickUncertaintyClasses must be populated

# Not used here (no cross-correlation in this template), but part of
# SolverOptions regardless -- see relocate_with_xcorr.py.
solver_cfg.xcorrWeightScaler = 2.0

# -----------------------------------------------------------------------
# 7. Group events into clusters, then relocate them.
#    saveProcessing=True dumps intermediate per-cluster/per-iteration data
#    to processingDataDir for debugging (extra disk I/O); leave
#    processingDataDir empty to auto-generate a directory name.
# -----------------------------------------------------------------------

clusters = dd.findClusters(cluster_cfg)

cat_new = dd.relocateMultiEvents(
    clusters,
    solver_cfg,
    saveProcessing=True,
    processingDataDir="",
)

# -----------------------------------------------------------------------
# 8. Save the relocated catalog. Pick ONE of the two options below.
#    How to evaluate the results: https://docs.gempa.de/scrtdd/current/base/multievent.html#evaluating-the-results
# -----------------------------------------------------------------------

# Option A: plain CSV files.
cat_new.writeToFile(
    "relocated-station.csv",
    "relocated-event.csv",
    "relocated-phase.csv",
)

# Option B: as an obspy Catalog instead (comment out Option A above if using
# this), e.g. to write QuakeML or to use obspy's own plotting (cat_new.plot()).
# Requires the obspy extra: pip install -v ".[obspy]"
# from pyrtdd.obspy.catalog import catalog_to_obspy
#
# obspy_cat_new = catalog_to_obspy(cat_new)
# obspy_cat_new.write("relocated.xml", format="QUAKEML")
