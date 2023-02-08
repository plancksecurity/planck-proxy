from setuptools import setup

setup(
    # keep aligned with setup.cfg
    setup_requires = [
        "setuptools >= 39.2.0",
        "setuptools_scm >= 4.1.2",
        "wheel",
    ],
    use_scm_version = {
        'write_to': "pepgate/__version__.py"
    },
    entry_points = { 'console_scripts': 'pepgate=pepgate.pEpgate:main' },
)
