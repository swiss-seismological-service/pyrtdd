
# stall libhdd header files.
SET(HDD_INSTALL_HEADERS OFF)

# Build libhdd as a shared library instead of static
SET(HDD_SHARED_LIB OFF)

# Build libhdd tests. This will be enabled also when SC_GLOBAL_UNITTESTS
SET(HDD_TESTS OFF)

# Build libhdd using boost::filesystem instead of std::filesystem
SET(HDD_USE_BOOST_FS OFF)

ADD_SUBDIRECTORY (scrtdd/libs/hdd)
