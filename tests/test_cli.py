"""
Tests for CLI interface
"""

import pytest
from click.testing import CliRunner
from src.cli import cli

def test_cli_help():
    """Test CLI help command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Trading Platform CLI' in result.output

def test_cli_start():
    """Test start command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['start'])
    assert result.exit_code == 0
    assert 'Starting Trading Platform' in result.output

def test_cli_status():
    """Test status command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'Platform status' in result.output
