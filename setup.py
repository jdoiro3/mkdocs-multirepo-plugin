from setuptools import find_packages
from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="mkdocs-multirepo-plugin",
    scripts=[
        'mkdocs_multirepo_plugin/scripts/sparse_clone.sh',
        'mkdocs_multirepo_plugin/scripts/sparse_clone_old.sh',
        'mkdocs_multirepo_plugin/scripts/mv_docs_up.sh'
        ],
    version="0.3.6",
    author="Joseph Doiron",
    author_email="josephdoiron1234@yahoo.com",
    description="Build documentation in multiple repos into one site.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    license="MIT",
    packages=find_packages(
        exclude=["tests"]
        ),
    install_requires=[
        "mkdocs>=1.0.4",
        "asyncio",
        "tqdm"
        ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "mkdocs.plugins": [
            "multirepo = mkdocs_multirepo_plugin.plugin:MultirepoPlugin"
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Documentation",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux"
    ],
)

