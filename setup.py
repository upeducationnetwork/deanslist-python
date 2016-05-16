from distutils.core import setup

setup(
    name='deanslist',
    version='0.1',
    packages=['deanslist'],
    url='https://github.com/upeducationnetwork/deanslist-python',
    license='',
    author='Ryan Knight',
    author_email='rknight@upeducationnetwork.org',
    description='Very basic wrapper for the Deanslist API',
    requires=['requests-futures']
)
