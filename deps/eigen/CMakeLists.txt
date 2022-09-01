CPMADDPACKAGE (
  NAME Eigen
  VERSION 3.4.0
  URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz
  DOWNLOAD_ONLY True
)

IF (eigen_ADDED)
  ADD_LIBRARY (eigen INTERFACE IMPORTED GLOBAL)
  TARGET_INCLUDE_DIRECTORIES (eigen INTERFACE ${eigen_SOURCE_DIR})
ENDIF ()
