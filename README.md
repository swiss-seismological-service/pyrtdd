# pyrtdd

Python wrapper for the C++ double-difference relocation library from [scrtdd](https://github.com/swiss-seismological-service/scrtdd).

# Installation

`pyrtdd` is tested with `gcc-11`, `gcc-12`, and `clang-14`. Before starting the installation process, please ensure that you have one of these compilers, along with [Anaconda](https://www.anaconda.com/products/distribution), installed on your system.

1. Clone this repository, ensuring that `scrtdd` is also pulled as a submodule:

    ```
    git clone --recursive https://github.com/swiss-seismological-service/pyrtdd.git
    ```

2. Create a `pyrtdd` Anaconda environment using the included `environment.yml` file:

    ```
    conda env create -n pyrtdd -f environment.yml
    ```

3. Activate the `pyrtdd` anaconda enviroment:

    ```
    conda activate pyrtdd
    ```

4. Install `pyrtdd` from source:

    ```
    CC=gcc-11 CXX=g++-11 SKBUILD_CONFIGURE_OPTIONS="-DCMAKE_C_COMPILER:STRING=gcc-11 -DCMAKE_CXX_COMPILER:STRING=g++-11" pip install -v .
    ```
    
# Installation notes

- The build process can take awhile: `pyrtdd` uses the [CPM](https://github.com/cpm-cmake/CPM.cmake) package management system to download Boost, a dependency of `scrtdd`. If you will be building the library a lot, be sure to check out the caching section of the CPM documentation.
- The entire build process is also outlined in the continuous integration (CI) process for this repository, which is described by the `.gitlab-ci.yml` file. The CI builds `pyrtdd` from a Ubuntu 22.04 base image, which can be reconstructed from the `Dockerfile.ci` file.


# Example

Please note that the code is in development stage. The documentation is not ready yet and you should use the [scrtdd](https://github.com/swiss-seismological-service/scrtdd) manual as a temporary reference. In particular, have a look at the [catalog format](https://docs.gempa.de/scrtdd/current/base/multievent.html#event-catalog-plain-csv-files) and the [relocation process](https://docs.gempa.de/scrtdd/current/base/multievent.html#relocation-process) paragraphs.



```python
from scrtdd.hdd import (
        Catalog,
        Config,
        ConstantVelocity,
        NLL,
        ObspyWaveformProxy,
        UTCClock,
        DD,
        SolverOptions,
        ClusteringOptions,
        NoWaveformProxy,
    )

cfg = Config()

#
# Defines a priority list of accepted P and S phases. Phases not in the list will be discarded from the catalog.
# If multiple phases exist for the same event at a station, the first one in the list will be used
# 
cfg.validPphases = ['Pg', 'P']
cfg.validSphases = ['Sg', 'S']

#
# Here we specify the input catalog. We use the test catalong for this example
#
cat = Catalog('./package/test/py/data/starting-station.csv',
              './package/test/py/data/starting-event.csv',
              './package/test/py/data/starting-phase.csv',
              False)

#
# Select the velocity model. There are two options available
#
ttt = ConstantVelocity(5.8, 3.36) # P/S velocity

# alternatively we can use NonLinLoc grids
#ttt = NLL('path/model/iasp91.PHASE.mod',
#          'path/time/iasp91.PHASE.STATION.time',
#          'path/time/iasp91.PHASE.STATION.angle',
#          False, # swap bytes
#          255)   # maximum number of files to keep open (performance stuff)

#
# Main class used for the relocation
#
dd = DD(cat, cfg, ttt, NoWaveformProxy())

#
# Define clustering options
# These options control which events and phases are used in the double-difference equation system. 
#
cluster_cfg = ClusteringOptions()

#
# Quality settings
# Allow to drop poorly connected events or bad phases
#
cluster_cfg.minNumNeigh = 4 # min neighbors required for an event
cluster_cfg.minDTperEvt = 8 # min differential times per event pair required (i.e. how many P+S phases)
cluster_cfg.minWeight = 0. # min weight of phases required (0-1). Uncertainties have to be included in the catalog

#
# Performance settings:
#  limit maxDTperEvt only if the relocation is too slow, otherwise keep them all 
#  maxNumNeigh doesn't usually improve results above 30-40
cluster_cfg.maxNumNeigh = 40 # max neighbors allowed. 0 -> disable
cluster_cfg.maxDTperEvt = 0 # max differential times per event pair required (Including P+S) 0 -> disable

#
# Station filtering
#
cluster_cfg.minEStoIEratio = 0. # min hypocenter-station to interevent distance ratio required
cluster_cfg.minESdist = 0. # min hypocenter-station distance required
cluster_cfg.maxESdist = -1 # max hypocenter-station distance allowed (-1 -> disable)

# Neighbours selection
# This option controls how neighbouring events are selected. In the simpliest form 'numEllipsoids'
# is set to 0 and 'maxNumNeigh' neighbours are selected on the nearest neighbour basis within a search
# distance of 'maxEllipsoidSize'. This is the default choice for multi-event mode.
# When 'numEllipsoids' is > 0, the ellipsoid selection algorithm from Waldhauser 2009: to assure a
# spatially homogeneous subsampling, reference events are selected within each of `numEllipsoids`
# concentric ellipsoidal layers of increasing thickness. Each layer is split up into its 8 quadrants
# (or cells), and the neighboring events are selected from each ellipsoid/quadrant combination in a
# round robin fashion until 'maxNumNeigh' is reached.
cluster_cfg.numEllipsoids = 0
cluster_cfg.maxEllipsoidSize = 5 # Km

# There is no cross-correlation binding to python yet :(
cluster_cfg.xcorrMaxEvStaDist = 0
cluster_cfg.xcorrMaxInterEvDist = 0
cluster_cfg.xcorrDetectMissingPhases = False

#
# Double-difference equations system solver configuration
#
solver_cfg = SolverOptions()

solver_cfg.type = "LSMR" # Solver algorithm to use: either LSMR or LSQR
solver_cfg.algoIterations = 20 # how many iterations the solver performs

solver_cfg.absLocConstraintStart = 0.3 # 0 -> disable absolute location constraint
solver_cfg.absLocConstraintEnd = 0.3   # 0 -> disable absolute location constraint
solver_cfg.dampingFactorStart = 0.01   # 0 -> disable damping factor
solver_cfg.dampingFactorEnd = 0.01     # 0 -> disable damping factor

solver_cfg.downWeightingByResidualStart = 10. # 0 -> disbale downweighting
solver_cfg.downWeightingByResidualEnd = 3.    # 0 -> disbale downweighting

solver_cfg.usePickUncertainty = False # if True then phase uncertaintis must be populated

# Air-quakes are events whose depth shift above the range of the velocity
# model (typically 0) during the inversion
solver_cfg.airQuakes.elevationThreshold = 0 # meters, threshold above which an event is considered an air-quake
solver_cfg.airQuakes.action = SolverOptions.AQ_ACTION.RESET_DEPTH # NONE, RESET or RESET_DEPTH

#
# Perform the relocation
#
cat_new = dd.relocateMultiEvents(cluster_cfg, solver_cfg)

#
# Write relocated catalog
#
cat_new.writeToFile('relocated-event.csv',
                    'relocated-phase.csv',
                    'relocated-station.csv')

```

![reloc](https://user-images.githubusercontent.com/15273575/205635799-80128f78-be04-48dc-8c17-32887d929552.png)



