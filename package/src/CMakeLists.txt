FIND_PACKAGE (
  Python
  COMPONENTS Interpreter Development.Module
  REQUIRED
)

EXECUTE_PROCESS (
  COMMAND "${Python_EXECUTABLE}" -c
          "import pybind11; print (pybind11.get_cmake_dir())"
  OUTPUT_VARIABLE _tmp_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ECHO STDOUT
)

LIST (APPEND CMAKE_PREFIX_PATH "${_tmp_dir}")
FIND_PACKAGE (pybind11 CONFIG REQUIRED)

INCLUDE_DIRECTORIES(${CMAKE_CURRENT_SOURCE_DIR}/../../deps/scrtdd/scrtdd/libs/hdd)


SET (HDD_EXT_DIR pyrtdd/hdd)
SET (
  SOURCES
  ${HDD_EXT_DIR}/ObspyWaveformProxy.cpp
  ${HDD_EXT_DIR}/hdd_ext.cpp
  ${HDD_EXT_DIR}/dd_ext.cpp
  ${HDD_EXT_DIR}/catalog_ext.cpp
  ${HDD_EXT_DIR}/ttt_ext.cpp
  ${HDD_EXT_DIR}/cvttt_ext.cpp
  ${HDD_EXT_DIR}/nllttt_ext.cpp
  ${HDD_EXT_DIR}/utc_clock_ext.cpp
)

PYBIND11_ADD_MODULE (hdd_ext MODULE ${SOURCES})
TARGET_LINK_LIBRARIES (hdd_ext PRIVATE hdd)
INSTALL (TARGETS hdd_ext LIBRARY DESTINATION ./hdd)
