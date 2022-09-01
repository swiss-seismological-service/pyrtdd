INCLUDE (CPM.cmake)

# Will be standardized.
ADD_SUBDIRECTORY (fmt) # formatting
ADD_SUBDIRECTORY (range-v3) # ranges before ranges
ADD_SUBDIRECTORY (tl-optional) # Mondaic optional.
ADD_SUBDIRECTORY (tl-expected) # Mondaic expected.

# External packages.
ADD_SUBDIRECTORY (catch2) # c++ testing framework
ADD_SUBDIRECTORY (eigen) # linear algebra
ADD_SUBDIRECTORY (google_benchmark) # benchmarking
ADD_SUBDIRECTORY (spdlog) # logging
