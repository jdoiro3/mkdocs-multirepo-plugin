from setuptools import find_packages
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="mkdocs-multirepo-plugin",
    scripts=['mkdocs_multirepo_plugin/sparse_checkout_docs.sh'],
    version="0.1.0",
    author="Joseph Doiron",
    author_email="josephdoiron1234@yahoo.com",
    description="Build documentation in multiple repos into one site.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    license="MIT",
    packages=find_packages(),
    install_requires=["mkdocs>=1.0.4"],
    extras_require={"test": ["pytest>=4.0", "pytest-cov"]},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "mkdocs.plugins": [
            "multirepo = mkdocs_multirepo_plugin.plugin:MultirepoPlugin"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Documentation",
    ],
)
