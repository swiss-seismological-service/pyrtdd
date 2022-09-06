FIND_PACKAGE (
  Python
  COMPONENTS Interpreter Development.Module
  REQUIRED
)

EXECUTE_PROCESS (
  COMMAND "${Python_EXECUTABLE}" -c
          "import nanobind; print (nanobind.cmake_dir())"
  OUTPUT_VARIABLE _tmp_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ECHO STDOUT
)

LIST (APPEND CMAKE_PREFIX_PATH "${_tmp_dir}")
FIND_PACKAGE (nanobind CONFIG REQUIRED)

SET (SOURCES nanobind_example_ext.cpp)
NANOBIND_ADD_MODULE (nanobind_example_ext NB_STATIC ${SOURCES})

INSTALL (TARGETS nanobind_example_ext LIBRARY DESTINATION .)
