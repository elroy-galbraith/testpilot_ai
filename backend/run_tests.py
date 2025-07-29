#!/usr/bin/env python3
"""
Test runner script for TestPilot AI Backend.
"""

import subprocess
import sys
import os

def run_tests(test_path=None, markers=None, verbose=False):
    """Run pytest with specified options."""
    cmd = ["python", "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    
    if markers:
        cmd.extend(["-m", markers])
    
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def main():
    """Main function to run tests based on command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [test_type]")
        print("Available test types:")
        print("  all          - Run all tests")
        print("  unit         - Run unit tests only")
        print("  integration  - Run integration tests only")
        print("  api          - Run API tests only")
        print("  auth         - Run authentication tests only")
        print("  coverage     - Run tests with coverage report")
        return
    
    test_type = sys.argv[1].lower()
    
    if test_type == "all":
        success = run_tests(verbose=True)
    elif test_type == "unit":
        success = run_tests(markers="unit", verbose=True)
    elif test_type == "integration":
        success = run_tests(markers="integration", verbose=True)
    elif test_type == "api":
        success = run_tests(markers="api", verbose=True)
    elif test_type == "auth":
        success = run_tests(markers="auth", verbose=True)
    elif test_type == "coverage":
        success = run_tests(verbose=True)
    else:
        print(f"Unknown test type: {test_type}")
        return
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 