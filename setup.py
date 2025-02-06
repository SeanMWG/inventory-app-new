from setuptools import setup, find_packages

setup(
    name="inventory-app",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-migrate',
        'flask-login',
        'flask-session',
        'msal',
        'python-dotenv',
        'gunicorn',
        'pyodbc',
    ]
)
