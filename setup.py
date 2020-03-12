from distutils.core import setup

setup(
    name="hacs-nexia-climate-integration",
    version="2.0.0BETA",
    packages=["custom_components/nexia"],
    url="https://github.com/ryannazaretian/hacs-nexia-climate-integration",
    license="GPL-3.0",
    author="ryannazaretian",
    install_requires=["requests","voluptuous"],
)
