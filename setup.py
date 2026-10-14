"""Installer for the collective.contact.widget package."""

from setuptools import setup

long_description = (
    open("README.rst").read() + "\n" + "Contributors\n"
    "============\n"
    + "\n"
    + open("CONTRIBUTORS.rst").read()
    + "\n"
    + open("CHANGES.rst").read()
    + "\n"
)


setup(
    name="collective.contact.widget",
    version="2.0.0.dev0",
    description="Contact widget",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.1",
        "Framework :: Plone :: 6.2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    keywords="plone contact widget field",
    author="Vincent Fretin",
    author_email="vincentfretin@ecreall.com",
    url="https://github.com/collective/collective.contact.widget",
    download_url="https://pypi.org/project/collective.contact.widget",
    license="GPL",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "plone.api",
        "plone.app.layout",
        "plone.base",
        "plone.schemaeditor",
        "plone.supermodel",
        "plone.uuid",
        "Products.CMFCore",
        "Products.ZCTextIndex",
        "z3c.form",
        "z3c.formwidget.query",
        "z3c.relationfield",
        "zc.relation",
        "Zope",
        "zope.intid",
    ],
    extras_require={
        "test": [
            "collective.contact.core",
            "plone.app.robotframework",
            "plone.app.testing",
            "plone.app.z3cform",
            "plone.testing",
            "robotsuite",
        ],
    },
    entry_points="""
    """,
)
