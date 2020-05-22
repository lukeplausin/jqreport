import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jqreport",
    version="0.0.1",
    author="Luke Plausin",
    author_email="lukeplausin@github.io",
    description="Build an HTML report out of any JSON data in seconds!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lukeplausin/jqreport",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7,>=3.6',
    entry_points = {
        'console_scripts': ['jqreport=jqreport.main:main'],
    },
    install_requires=[
        'jinja2',
        'pyyaml'
    ]
)
