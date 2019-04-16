from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf8') as f:
    readme = f.read()

setup(
    name="m2",
    version="2019.1-dev",
    packages=find_packages(exclude=("tests*",)),
    author="mdrachuk",
    author_email="misha@drach.uk",
    description="Easily serialize dataclasses to and from JSON",
    long_description=readme,
    long_description_content_type='text/markdown',
    url="https://github.com/mdrachuk/m2",
    license="Unlicense",
    keywords="dataclasses json marshalling",
    install_requires=[
        "dataclasses;python_version=='3.6'",
        "marshmallow>=3.0.0b20"
    ],
    python_requires=">=3.6",
    extras_require={
        "dev": ["pytest", "ipython", "mypy", "hypothesis"]
    },
    include_package_data=True
)
