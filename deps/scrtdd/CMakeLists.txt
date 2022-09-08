SET (SC3_PACKAGE_SOURCE_DIR ${CMAKE_CURRENT_LIST_DIR}/scrtdd)

SET (
  COMPILE_ADAPTERS
  OFF
  CACHE BOOL "Skip compilation of adapters" FORCE
)

SET (
  HDD_SHARED_LIB
  OFF
  CACHE BOOL "BUILD a static version of the HDD lib" FORCE
)

ADD_SUBDIRECTORY (scrtdd/libs/hdd)
