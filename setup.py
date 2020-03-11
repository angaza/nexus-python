import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nexus_keycode",
    packages=setuptools.find_packages(),
    license="MIT",
    version="1.0.2",
    author="Angaza, Inc.",
    author_email="iot@angaza.com",
    description="The Angaza Nexus Keycode for PAYG devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/angaza/nexus-keycode-python",
    download_url="https://github.com/angaza/nexus-keycode-python/releases/download/1.0.2/nexus_keycode-1.0.2.tar.gz",
    install_requires=[
        "bitstring>=3.0.2",
        "enum34==1.1.6",
        "nose2==0.9.2",
        "siphash==0.0.1",
    ],
    test_suite="nose2.collector",
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=2.7, >=3.6",
)