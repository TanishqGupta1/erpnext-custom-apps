from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="chat_bridge",
    version="1.0.0",
    description="Unified Chat integration for ERPNext Support, CRM, and NextCRM",
    author="VisualGraphX",
    author_email="dev@visualgraphx.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[],
)

