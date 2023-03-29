import sys

try:
    from skbuild import setup
    import pybind11
except ImportError:
    print(
        "The preferred way to invoke 'setup.py' is via pip, as in 'pip "
        "install .'. If you wish to run the setup script directly, you must "
        "first install the build dependencies listed in pyproject.toml!",
        file=sys.stderr,
    )
    raise

setup(
    name="pyrtdd",
    version="0.0.1",
    author="Luca Scarabello, Mondaic Ltd.",
    author_email="luca.scarabello@erdw.ethz.ch, support@mondaic.com",
    url="https://github.com/swiss-seismological-service/pyrtdd",
    description="Double-difference earthquake relocation",
    long_description="Python wrapper for the C++ double-difference relocation library from scrtdd",
    packages=["pyrtdd", "pyrtdd.hdd"],
    package_dir={"": "package/src"},
    cmake_install_dir="package/src/pyrtdd",
    include_package_data=True,
    extras_require={"test": ["pytest"]},
    install_requires=["numpy>=1.23.3", "obspy>=1.3.0"],
    python_requires=">=3.8",
)
