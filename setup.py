from setuptools import setup

setup(
    name='PyChat',
    version='1.0',
    packages=['client', 'server', 'http_classes', "gui_templates"],
    url='https://github.com/VityasZV/JointPython/',
    license='WTFPL',
    author='JointPythonTeam',
    description='Small chat',
    install_requires=["PyQt5", "psycopg2", "urllib3", "requests"],
)
