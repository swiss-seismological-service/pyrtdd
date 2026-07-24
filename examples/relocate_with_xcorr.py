"""pyrtdd relocation template -- WITH cross-correlation.

Same multi-event relocation workflow as relocate.py, plus everything needed
for cross-correlation: a waveform source, waveform preprocessing, and the
full XcorrOptions configuration, with every option documented in the
README's "Cross-correlation" section, using their defaults.

Requires the `obspy` extra: pip install -v ".[obspy]"

Fields you must fill in yourself are marked "# TODO". Everything else is a
tunable default copied from the README -- read the corresponding README
section before changing it, since most of these interact with each other.

If you don't need cross-correlation, see relocate.py instead (simpler, no
obspy dependency).

Usage:
    python examples/relocate_with_xcorr.py
"""

import obspy

from pyrtdd.hdd import (
    Catalog,
    Config,
    Homogeneous,
    NLLGrid,
    ClusteringOptions,
    SolverOptions,
    XcorrOptions,
    XCorrCache,
    DD,
    Logger,
)
from pyrtdd.obspy.waveform import StreamProxy, ObspyClientProxy, FileScannerProxy

PhaseType = Catalog.Phase.Type

# -----------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------

# debug, info (default), warning, error, or none (disables logging entirely)
Logger.setLevel(Logger.Level.info)

# -----------------------------------------------------------------------
# 1. Load the input catalog: stations, events, and phase picks.
#    Format: https://docs.gempa.de/scrtdd/current/base/multievent.html#event-catalog-plain-csv-files
# -----------------------------------------------------------------------

cat = Catalog(
    "<path/to/station.csv>",  # TODO
    "<path/to/event.csv>",  # TODO
    "<path/to/phase.csv>",  # TODO
)

# -----------------------------------------------------------------------
# 2. Phase catalog configuration: controls which picks are actually used,
#    plus waveform preprocessing for cross-correlation (cfg.wfFilter).
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

# Preprocessing applied to waveforms loaded for cross-correlation. Every
# trace is demeaned automatically first, regardless of these settings;
# resampling then filtering happen after that, in that order, only if
# configured below.
cfg.wfFilter.resampleFreq = 0  # resample to this rate [Hz] before filtering. 0 -> no resampling
cfg.wfFilter.filterStr = ""  # filter to apply, in the "<type>;key=val;key=val;..." mini-syntax
                              #  a WaveformProxy.filter() implementation is handed. "" -> no
                              #  filtering (default). pyrtdd.obspy.waveform's proxies map this
                              #  directly onto obspy's Trace.filter(type, **kwargs), e.g.
                              #  "bandpass;freqmin=1;freqmax=10;corners=4"
cfg.wfFilter.extraTraceLen = 1  # extra secs of data loaded before and after the needed window,
                                 #  trimmed off again after resampling/filtering -- gives the
                                 #  filter room to settle and avoids edge artifacts in the window
                                 #  actually used for cross-correlation

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
#     maxSearchDistance=0.1,  # max distance [m] allowed between a queried station's
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
# 4. Waveform source: pick ONE of the three options below.
#
#    All three need an obspy.Inventory (StationXML) to resolve channel
#    orientation for the R/T/L2 cross-correlation component transforms
#    ("L2" is the default for S phases, so this is needed even for the
#    default XcorrOptions config below). Can be None if you don't have
#    one, provided guess_zne=True (otherwise orientation resolution raises
#    whenever it's actually needed).
# -----------------------------------------------------------------------

inventory = obspy.read_inventory("<path/to/inventory.xml>")  # TODO, or set to None
guess_zne = False  # fall back to a guessed Z/N/E layout instead of raising
                    #  when a channel's orientation can't be resolved

# Option A: wrap waveforms already loaded into an obspy.Stream.
# stream = obspy.read("<path/to/waveforms>")  # TODO
# proxy = StreamProxy(stream, inventory, guess_zne=guess_zne)

# Option B: wrap any obspy client exposing get_waveforms(net, sta, loc, cha, t0, t1),
# e.g. obspy.clients.filesystem.sds.Client, obspy.clients.fdsn.Client, or
# obspy.clients.earthworm.Client. get_waveforms_bulk is used automatically to
# preload/cache requests in a single call when the client supports it (e.g. FDSN);
# it falls back to one get_waveforms call per trace otherwise (e.g. SDS, Earthworm).
from obspy.clients.filesystem.sds import Client as SDSClient  # or obspy.clients.fdsn.Client, etc.

client = SDSClient("<path/to/sds_archive>")  # TODO
proxy = ObspyClientProxy(client, inventory, guess_zne=guess_zne)

# Option C: scan a local folder for waveform files (any format obspy can read,
# e.g. miniSEED) and serve them like an archive. Indexed once at construction
# time (header-only read); files added afterward aren't picked up. Waveform
# data is read from disk on demand per request, never held in memory.
# proxy = FileScannerProxy(
#     "<path/to/waveforms>",  # TODO: folder to scan
#     inventory,
#     guess_zne=guess_zne,
#     recursive=True,  # also scan subfolders. If False, only the top-level folder is scanned
# )

# -----------------------------------------------------------------------
# 5. Build the relocator.
# -----------------------------------------------------------------------

dd = DD(cat, cfg, ttt, proxy)

# Optional: cache fetched waveforms to disk, and read from there instead of
# re-fetching on later runs. Worth enabling whenever fetching waveforms is
# slower than computing the cross-correlation itself, which is common:
# FDSNWS pays a network round trip per request, SDS/folder archives on a
# network-mounted filesystem pay network/filesystem latency per read, and
# even a fast local archive can become the bottleneck with many phases.
# dd.enableCatalogWaveformDiskCache(
#     "<path/to/waveform_cache>",  # TODO
#     diskTraceMinLen=10.0,  # min secs of data cached around each pick, regardless of how
#                             #  short the xcorr window itself needs; a wider cached window
#                             #  than any single xcorr_cfg setting needs means later changes
#                             #  to its window offsets can often still hit the cache
# )

# -----------------------------------------------------------------------
# 6. Clustering: controls which events/phases enter the double-difference
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
cluster_cfg.minEvStaToInterEvRatio = 0.0  # min hypocenter-station to interevent distance ratio
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
# 7. Cross-correlation configuration.
# -----------------------------------------------------------------------

xcorr_cfg = XcorrOptions()
xcorr_cfg.enable = True

# Station filtering (this can be more restrictive than the clustering phase)
xcorr_cfg.minEvStaDist = 0  # min event to station distance
xcorr_cfg.maxEvStaDist = -1  # max event to station distance. -1 -> disable
xcorr_cfg.maxInterEvDist = -1  # max inter-event distance. -1 -> disable

# Per-phase-type settings (defaults shown)
xcorr_cfg.phase[PhaseType.P].minCoef = 0.70  # min cross-correlation coefficient required (0-1)
xcorr_cfg.phase[PhaseType.P].startOffset = -0.50  # xcorr window start: secs before the pick
xcorr_cfg.phase[PhaseType.P].endOffset = 0.50  # xcorr window end: secs after the pick
xcorr_cfg.phase[PhaseType.P].winScaling = 0.02  # window scaling coefficient:
                                                 #  windowLength = (endOffset - startOffset) + travelTime * winScaling
xcorr_cfg.phase[PhaseType.P].maxDelay = 0.50  # max allowed lag between the two traces being
                                               #  cross-correlated, secs
xcorr_cfg.phase[PhaseType.P].components = ["Z"]  # priority list of components to try, in order,
                                                  #  until one succeeds. Each entry is either a
                                                  #  literal orientation code (e.g. "Z"), or one of
                                                  #  the computed transforms "R" (radial), "T"
                                                  #  (transversal), "L2" (need channel orientation
                                                  #  info, i.e. `inventory` above)

xcorr_cfg.phase[PhaseType.S].minCoef = 0.70
xcorr_cfg.phase[PhaseType.S].startOffset = -0.50
xcorr_cfg.phase[PhaseType.S].endOffset = 1.00
xcorr_cfg.phase[PhaseType.S].winScaling = 0.04
xcorr_cfg.phase[PhaseType.S].maxDelay = 0.50
xcorr_cfg.phase[PhaseType.S].components = ["L2"]

# -----------------------------------------------------------------------
# 8. Solver: double-difference equations system solver configuration.
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
solver_cfg.xcorrWeightScaler = 2.0  # scales the weight given to cross-correlation-derived
                                     #  observations

# -----------------------------------------------------------------------
# 9. Group events into clusters, then relocate them.
#    saveProcessing=True dumps intermediate per-cluster/per-iteration data
#    (including the cross-correlation cache) to processingDataDir for
#    debugging (extra disk I/O); leave processingDataDir empty to
#    auto-generate a directory name.
# -----------------------------------------------------------------------

clusters = dd.findClusters(cluster_cfg)

# xcorr_data gets populated with the computed coefficients/lags as a side
# effect, which you can reuse in a later call to skip recomputing pairs it
# already has entries for -- pick ONE of the two options below. Reusing a
# cache like this only pays off for pairs it already has entries for: any
# event/station/phase combination it doesn't cover still gets
# cross-correlated normally (and is added to xcorr_data as usual).

# Option A: start with an empty cache (default).
xcorr_data = XCorrCache()

# Option B: reload results computed by an earlier run instead of recomputing
# them from scratch (comment out Option A above if using this). `cat` must
# be the same background catalog the cache was originally computed against.
# xcorr_data = XCorrCache.readFromFile(cat, "<path/to/xcorr_cache.csv>")  # TODO

cat_new = dd.relocateMultiEvents(
    clusters,
    xcorr_data,
    xcorr_cfg,
    solver_cfg,
    saveProcessing=True,
    processingDataDir="",
)

# Optional: save cross-correlation results to reuse them in a later call
# (skip this if saveProcessing=True already stored a copy in processingDataDir).
xcorr_data.writeToFile(cat, "xcorr_cache.csv")

# -----------------------------------------------------------------------
# 10. Save the relocated catalog.
#     How to evaluate the results: https://docs.gempa.de/scrtdd/current/base/multievent.html#evaluating-the-results
# -----------------------------------------------------------------------

cat_new.writeToFile(
    "relocated-event.csv",
    "relocated-phase.csv",
    "relocated-station.csv",
)
