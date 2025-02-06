#!/usr/bin/env python3
"""Development helper script."""
import os
import sys
import subprocess
import click
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent.resolve()

# Virtual environment paths
if os.name == 'nt':  # Windows
    VENV_PYTHON = ROOT_DIR / 'venv' / 'Scripts' / 'python.exe'
    VENV_PIP = ROOT_DIR / 'venv' / 'Scripts' / 'pip.exe'
    VENV_FLASK = ROOT_DIR / 'venv' / 'Scripts' / 'flask.exe'
else:  # Unix-like
    VENV_PYTHON = ROOT_DIR / 'venv' / 'bin' / 'python'
    VENV_PIP = ROOT_DIR / 'venv' / 'bin' / 'pip'
    VENV_FLASK = ROOT_DIR / 'venv' / 'bin' / 'flask'

@click.group()
def cli():
    """Development helper script."""
    pass

@cli.command()
@click.option('--coverage/--no-coverage', default=True, help='Run with coverage report')
@click.option('--verbose/--no-verbose', default=False, help='Verbose output')
def test(coverage, verbose):
    """Run tests."""
    cmd = [str(VENV_PYTHON), '-m', 'pytest']
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=term-missing'])
    if verbose:
        cmd.append('-v')
    
    click.echo('Running tests...')
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

@cli.command()
def lint():
    """Run linters."""
    click.echo('Running flake8...')
    flake8_result = subprocess.run([str(VENV_PYTHON), '-m', 'flake8', 'src', 'tests'])
    
    click.echo('Running mypy...')
    mypy_result = subprocess.run([str(VENV_PYTHON), '-m', 'mypy', 'src'])
    
    if flake8_result.returncode != 0 or mypy_result.returncode != 0:
        sys.exit(1)

@cli.command()
@click.option('--check', is_flag=True, help='Check if files would be reformatted')
def format(check):
    """Format code with black."""
    cmd = [str(VENV_PYTHON), '-m', 'black']
    if check:
        cmd.append('--check')
    cmd.extend(['src', 'tests'])
    
    click.echo('Running black...')
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

@cli.command()
def clean():
    """Clean up generated files."""
    patterns = [
        '**/__pycache__',
        '**/*.pyc',
        '**/*.pyo',
        '**/*.pyd',
        '.pytest_cache',
        '.coverage',
        'coverage_html',
        'dist',
        'build',
        '*.egg-info'
    ]
    
    click.echo('Cleaning up...')
    for pattern in patterns:
        for path in ROOT_DIR.glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)

@cli.command()
def setup():
    """Set up development environment."""
    click.echo('Creating virtual environment...')
    if not os.path.exists('venv'):
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
    
    click.echo('Installing dependencies...')
    subprocess.run([str(VENV_PIP), 'install', '-r', 'requirements.txt'])
    
    click.echo('Installing package in development mode...')
    subprocess.run([str(VENV_PIP), 'install', '-e', '.'])
    
    click.echo('Initializing database...')
    subprocess.run([str(VENV_PYTHON), 'init_db.py'])
    
    click.echo('Development environment setup complete!')

@cli.command()
def run():
    """Run development server."""
    os.environ['FLASK_APP'] = 'src.app:app'
    os.environ['FLASK_ENV'] = 'development'
    subprocess.run([str(VENV_FLASK), 'run', '--debug'])

@cli.command()
def shell():
    """Run Flask shell."""
    os.environ['FLASK_APP'] = 'src.app:app'
    subprocess.run([str(VENV_FLASK), 'shell'])

@cli.command()
@click.argument('message')
def revision(message):
    """Create a new database migration revision."""
    os.environ['FLASK_APP'] = 'src.app:app'
    subprocess.run([str(VENV_FLASK), 'db', 'migrate', '-m', message])

@cli.command()
def upgrade():
    """Upgrade database to latest revision."""
    os.environ['FLASK_APP'] = 'src.app:app'
    subprocess.run([str(VENV_FLASK), 'db', 'upgrade'])

@cli.command()
def downgrade():
    """Downgrade database by one revision."""
    os.environ['FLASK_APP'] = 'src.app:app'
    subprocess.run([str(VENV_FLASK), 'db', 'downgrade'])

@cli.command()
@click.option('--check/--no-check', default=True, help='Run checks before building')
def build(check):
    """Build the application."""
    if check:
        click.echo('Running tests...')
        test_result = subprocess.run([str(VENV_PYTHON), '-m', 'pytest'])
        if test_result.returncode != 0:
            click.echo('Tests failed, aborting build')
            sys.exit(1)
        
        click.echo('Running linters...')
        lint_result = subprocess.run([str(VENV_PYTHON), '-m', 'flake8', 'src'])
        if lint_result.returncode != 0:
            click.echo('Linting failed, aborting build')
            sys.exit(1)
    
    click.echo('Building application...')
    subprocess.run([str(VENV_PYTHON), '-m', 'build'])

if __name__ == '__main__':
    cli()
