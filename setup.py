import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="netcore",
    version="0.1.3-alpha-2",
    author="Aiden Hopkins",
    author_email="acdphc@qq.com",
    description="A Network Protocol Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/A03HCY/Netcore",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)