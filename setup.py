import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="autotransform",
    version="0.0.1",
    author="Nathan Rockenbach",
    author_email="nathro.software@gmail.com",
    description="A component based tool for designing automated code modification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nathro/AutoTransform",
    project_urls={
        "Bug Tracker": "https://github.com/nathro/AutoTransform/issues",
        "Source": "https://github.com/nathro/AutoTransform/",
        "Say Thanks": "https://saythanks.io/to/nathro.software",
        "Support": "https://www.paypal.com/paypalme/nathrosoftware",
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Codemod',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='codemod, automation, code change',
    package_dir={"": "autotransform"},
    packages=setuptools.find_packages(where="autotransform"),
    install_requires=[
        'GitPython',
        'PyGithub'
    ],
    python_requires=">=3.10",
)