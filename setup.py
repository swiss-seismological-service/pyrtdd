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
    name="scrtdd",
    version="0.0.1",
    author="Mondaic Ltd.",
    author_email="support@mondaic.com",
    description="Python bindings for the SED's `scrtdd` library",
    url="https://gitlab.com/Mondaic/Projects/sed-dug-seis/scrtdd-wrappers",
    packages=["scrtdd", "scrtdd.hdd"],
    package_dir={"": "package/src"},
    cmake_install_dir="package/src/scrtdd",
    include_package_data=True,
    extras_require={"test": ["pytest"]},
    python_requires=">=3.8",
)
