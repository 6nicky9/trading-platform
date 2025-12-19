"""
Tests for Docker compatibility and configuration
"""

import yaml
import toml
import pytest
import os

def test_docker_compose_valid():
    """Test that docker-compose.yml is valid YAML"""
    with open("docker-compose.yml", "r") as f:
        content = yaml.safe_load(f)
    
    assert "version" in content
    assert content["version"] == "3.8"
    assert "services" in content
    assert "postgres" in content["services"]
    assert "redis" in content["services"]
    assert "trading-app" in content["services"]
    
    print("✓ docker-compose.yml is valid")

def test_dockerfile_exists():
    """Test that Dockerfile exists and has basic content"""
    assert os.path.exists("docker/Dockerfile")
    
    with open("docker/Dockerfile", "r") as f:
        content = f.read()
    
    assert "FROM python:3.10-slim" in content
    assert "WORKDIR /app" in content
    assert "COPY requirements.txt" in content
    assert "RUN pip install" in content
    
    print("✓ Dockerfile is valid")

def test_pyproject_toml_valid():
    """Test that pyproject.toml is valid"""
    with open("pyproject.toml", "r") as f:
        content = toml.load(f)
    
    assert "project" in content
    assert "name" in content["project"]
    assert content["project"]["name"] == "trading-platform"
    assert "dependencies" in content["project"]
    
    print("✓ pyproject.toml is valid")

def test_requirements_txt_exists():
    """Test that requirements.txt exists"""
    assert os.path.exists("requirements.txt")
    
    with open("requirements.txt", "r") as f:
        content = f.read()
    
    # Check for key dependencies
    assert "fastapi" in content
    assert "uvicorn" in content
    assert "pytest" in content
    
    print("✓ requirements.txt is valid")

def test_makefile_commands():
    """Test that Makefile has essential commands"""
    with open("Makefile", "r") as f:
        content = f.read()
    
    assert "make build" in content
    assert "make up" in content
    assert "make down" in content
    assert "make test" in content
    
    print("✓ Makefile is valid")
