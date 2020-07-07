from setuptools import setup, find_packages

setup(
    name='PyChat',
    description='Simple Python chat app',
    version='0.9',
    packages=find_packages(),
    url='https://github.com/VityasZV/JointPython',
    license='WTFPL',
    author='JointPythonTeam',
    install_requires=["PyQt5", "psycopg2", "urllib3", "requests"]
)
