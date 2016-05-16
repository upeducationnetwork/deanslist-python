from distutils.core import setup

setup(
    name='deanslist',
    version='0.1.1',
    packages=['deanslist'],
    url='https://github.com/upeducationnetwork/deanslist-python',
    license='MIT',
    author='Ryan Knight',
    author_email='rknight@upeducationnetwork.org',
    description='Very basic wrapper for the Deanslist API',
    install_requires=['requests-futures']
)
