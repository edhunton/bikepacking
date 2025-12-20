#!/usr/bin/env python3
"""Test script to verify Square SDK installation."""
import sys

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print()

try:
    from square.client import Client
    print("✅ Square SDK is installed and can be imported!")
    print(f"   Client class: {Client}")
except ImportError as e:
    print("❌ Square SDK is NOT installed or cannot be imported")
    print(f"   Error: {e}")
    print()
    print("To install:")
    print("   pip install squareup")


