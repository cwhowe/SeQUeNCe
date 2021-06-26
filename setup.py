from setuptools import setup

setup(
    name="sequence",
    version="0.2.3",
    author="Xiaoliang Wu, Joaquin Chung, Alexander Kolar, Alexander Kiefer, Eugene Wang, Tian Zhong, Rajkumar Kettimuthu, Martin Suchara",
    author_email="xwu64@hawk.iit.edu, chungmiranda@anl.gov, akolar@anl.gov, akiefer@iu.edu, eugenewang@yahoo.com, tzh@uchicago.edu, kettimut@mcs.anl.gov, msuchara@anl.gov",
    description="Simulator of Quantum Network Communication: SEQUENCE-Python is a prototype version of the official SEQUENCE release.",
    # packages = find_packages('src'),
    packages=['sequence', 'sequence.app', 'sequence.kernel', 'sequence.components',
              'sequence.network_management', 'sequence.entanglement_management', 'sequence.qkd',
              'sequence.resource_management', 'sequence.topology', 'sequence.utils', 'sequence.gui'],
    package_dir={'sequence': 'src'},
    include_package_data=True,
    install_requires=[
        'numpy',
	    'matplotlib',
        'json5',
        'pandas',
        'qutip',
        'dash',
        'dash-core-components',
        'dash-html-components',
        'dash-bootstrap-components',
        'networkx',
        'dash-table',
        'dash-cytoscape',
        'plotly',
    ],
)
