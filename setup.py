import os

from setuptools import find_packages, setup


###############################################################################

NAME = "matomo"
PACKAGES = find_packages(where="src")
META_PATH = os.path.join("src", "matomo", "__init__.py")
KEYWORDS = ["matomo",]
PROJECT_URLS = {
    "Bug Tracker": "https://github.com/samastur/matomo/issues",
    "Source Code": "https://github.com/samastur/matomo",
}
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: Implementation :: CPython",
]
INSTALL_REQUIRES = [
    "requests>=2.*"
]

###############################################################################

AUTHOR = "Marko Samastur"
AUTHOR_EMAIL = "matomo@markos.gaivo.net"
VERSION = "0.5"
LICENSE = "MIT"
URL = "https://github.com/samastur/matomo"
DESCRIPTION = "Python Matomo client API"
LONG = (
    "This is a Python implementation of the Matomo tracking and analytics APIs "
    "based on PHP version with an almost 100% compatible API."
)


if __name__ == "__main__":
    setup(
        name="matomo",
        description=DESCRIPTION,
        license=LICENSE,
        url=URL,
        project_urls=PROJECT_URLS,
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        maintainer=AUTHOR,
        maintainer_email=AUTHOR_EMAIL,
        keywords=KEYWORDS,
        long_description=LONG,
        packages=PACKAGES,
        package_dir={"": "src"},
        python_requires=">=3.6",
        zip_safe=False,
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
        options={"bdist_wheel": {"universal": "1"}},
    )
