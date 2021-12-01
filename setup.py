from setuptools import setup, find_packages

"""
https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration
"""

setup(
    name='balance_projector',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        'attrs',
        'python-dateutil',
        'PyYAML',
        'click',
        'tabulate'
    ],
    extras_require={
        'dev': [
            'nose2',
            'parameterized',
            'coverage'
        ]
    },
    entry_points='''
        [console_scripts]
        projector=balance_projector.__main__:cli
    ''',
)
