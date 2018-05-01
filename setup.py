from setuptools import setup

setup(
    name='configclasses',
    version='0.4.1',
    description='Strongly typed configuration classes made simple and effective.',
    url='http://github.com/jeffbelgum/configclasses',
    author='Jeff Belgum',
    author_email='jeffbelgum@gmail.com',
    license='MIT/APACHE-2.0',
    packages=['configclasses'],
    install_requires=[
        'dataclasses>=0.4',
        'requests>=2.18.4',
        'toml>=0.9.4',
    ],
    extras_require={
        'dev': [],
        'test': ['pytest', 'pytest-cov'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='configuration settings config environment typed dataclasses',
    python_requires='>=3.6',
)
