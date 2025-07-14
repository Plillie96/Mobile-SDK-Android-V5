#!/usr/bin/env python3
"""
Test script to verify Kraken Trading Bot installation
"""

import sys
import importlib
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing package imports...")
    
    required_packages = [
        'numpy',
        'pandas',
        'ccxt',
        'krakenex',
        'ta',
        'sklearn',
        'joblib',
        'aiohttp',
        'fastapi',
        'uvicorn',
        'plotly',
        'dash',
        'dash_bootstrap_components',
        'pydantic',
        'python-dotenv'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError as e:
            print(f"✗ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\nFailed to import: {failed_imports}")
        print("Please install missing packages with: pip install -r requirements.txt")
        return False
    else:
        print("\nAll packages imported successfully!")
        return True

def test_bot_imports():
    """Test if bot modules can be imported"""
    print("\nTesting bot module imports...")
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.append(str(src_path))
    
    bot_modules = [
        'config',
        'src.exchange',
        'src.technical_analysis',
        'src.machine_learning',
        'src.risk_management',
        'src.trading_bot',
        'src.dashboard'
    ]
    
    failed_imports = []
    
    for module in bot_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nFailed to import bot modules: {failed_imports}")
        return False
    else:
        print("\nAll bot modules imported successfully!")
        return True

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import config
        print("✓ Configuration loaded successfully")
        print(f"  Trading pairs: {config.trading_pairs}")
        print(f"  Max position size: {config.max_position_size}")
        print(f"  Stop loss: {config.stop_loss_percentage}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_directory_structure():
    """Test if required directories exist"""
    print("\nTesting directory structure...")
    
    required_dirs = ['src', 'models', 'logs']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✓ {dir_name}/")
        else:
            print(f"✗ {dir_name}/ (will be created automatically)")
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"\nMissing directories: {missing_dirs}")
        print("These will be created automatically when the bot runs.")
    
    return True

def main():
    """Run all tests"""
    print("Kraken Trading Bot - Installation Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_bot_imports,
        test_configuration,
        test_directory_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("Test Results Summary")
    print("=" * 40)
    
    if all(results):
        print("🎉 All tests passed! The bot is ready to use.")
        print("\nNext steps:")
        print("1. Run 'python main.py --setup' to create configuration template")
        print("2. Edit .env file with your Kraken API credentials")
        print("3. Run 'python main.py --with-dashboard' to start the bot")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Check Python version (requires 3.8+)")
        print("3. Verify all files are in the correct locations")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)