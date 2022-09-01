CPMADDPACKAGE (
  NAME range-v3
  URL https://github.com/ericniebler/range-v3/archive/refs/tags/0.12.0.tar.gz
  DOWNLOAD_ONLY True
)

IF (range-v3_ADDED)
  ADD_LIBRARY (range-v3 INTERFACE IMPORTED)
  TARGET_INCLUDE_DIRECTORIES (
    range-v3 INTERFACE "${range-v3_SOURCE_DIR}/include"
  )
ENDIF ()
