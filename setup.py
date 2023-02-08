import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="acdpnet",
    version="2.3.2",
    author="Aiden Hopkins",
    author_email="acdphc@qq.com",
    description="A Network Protocol Frame",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/A03HCY/Network-Core",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)