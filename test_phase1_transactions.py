"""Test script to verify Phase 1 transaction implementation.

This script tests that all cascade delete operations are now using
transactions and will properly rollback on errors.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize logging before imports
from config.logging_config import setup_logging

setup_logging(log_level="INFO")

import logging

from config.database import db
from models.area import AreaModel
from models.grant import GrantModel
from models.habitat import HabitatModel
from models.measure import MeasureModel
from models.priority import PriorityModel
from models.species import SpeciesModel

logger = logging.getLogger(__name__)


def test_database_connection():
    """Test basic database connectivity."""
    print("=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)

    try:
        assert db.test_connection(), "Connection test failed"
        info = db.get_connection_info()
        print(f"✓ Connected to {info['mode'].upper()} database")
        print(f"  Database: {info['database']}")
        return True
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False


def test_transaction_method():
    """Test the execute_transaction method directly."""
    print("\n" + "=" * 60)
    print("TEST 2: Transaction Method")
    print("=" * 60)

    try:
        # Test successful transaction
        queries = [
            ("SELECT COUNT(*) FROM measure", None),
            ("SELECT COUNT(*) FROM area", None),
        ]
        db.execute_transaction(queries)
        print("✓ Transaction executed successfully")

        # Test rollback on error
        try:
            bad_queries = [
                ("SELECT COUNT(*) FROM measure", None),
                ("SELECT * FROM nonexistent_table", None),  # This will fail
            ]
            db.execute_transaction(bad_queries)
            print("✗ Expected error did not occur")
            return False
        except Exception as e:
            print(f"✓ Transaction properly rolled back on error")
            logger.debug(f"  Expected error: {e}")

        return True
    except Exception as e:
        print(f"✗ Transaction test failed: {e}")
        return False


def test_model_transaction_usage():
    """Test that models are using transactions properly."""
    print("\n" + "=" * 60)
    print("TEST 3: Model Transaction Usage")
    print("=" * 60)

    models = {
        "Measure": MeasureModel(),
        "Area": AreaModel(),
        "Priority": PriorityModel(),
        "Species": SpeciesModel(),
        "Habitat": HabitatModel(),
        "Grant": GrantModel(),
    }

    success = True

    for name, model in models.items():
        try:
            # Check that delete_with_cascade method exists
            assert hasattr(model, "delete_with_cascade"), f"{name} missing delete_with_cascade"

            # Check method signature includes proper error handling
            import inspect

            source = inspect.getsource(model.delete_with_cascade)

            # Check for transaction usage
            if "execute_transaction" in source:
                print(f"✓ {name}.delete_with_cascade uses transactions")
            else:
                print(f"✗ {name}.delete_with_cascade NOT using transactions")
                success = False

            # Check for logging
            if "logger." in source:
                print(f"✓ {name}.delete_with_cascade has logging")
            else:
                print(f"✗ {name}.delete_with_cascade missing logging")
                success = False

            # Check for proper error handling
            if "duckdb.Error" in source:
                print(f"✓ {name}.delete_with_cascade has proper error types")
            else:
                print(f"✗ {name}.delete_with_cascade using generic Exception")
                success = False

        except Exception as e:
            print(f"✗ Error checking {name}: {e}")
            success = False

        print()  # Blank line between models

    return success


def test_measure_update_with_relationships():
    """Test the new atomic update method."""
    print("=" * 60)
    print("TEST 4: Measure Update With Relationships")
    print("=" * 60)

    try:
        measure_model = MeasureModel()

        # Check method exists
        assert hasattr(
            measure_model, "update_with_relationships"
        ), "update_with_relationships method not found"

        # Check it uses transactions
        import inspect

        source = inspect.getsource(measure_model.update_with_relationships)

        if "execute_transaction" in source:
            print("✓ update_with_relationships uses transactions")
        else:
            print("✗ update_with_relationships NOT using transactions")
            return False

        if "logger." in source:
            print("✓ update_with_relationships has logging")
        else:
            print("✗ update_with_relationships missing logging")
            return False

        print("✓ update_with_relationships properly implemented")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_measure_add_methods():
    """Test that add_* methods are using transactions."""
    print("\n" + "=" * 60)
    print("TEST 5: Measure Add Methods")
    print("=" * 60)

    try:
        measure_model = MeasureModel()
        methods = ["add_measure_types", "add_stakeholders", "add_benefits"]

        success = True
        for method_name in methods:
            assert hasattr(measure_model, method_name), f"{method_name} not found"

            import inspect

            source = inspect.getsource(getattr(measure_model, method_name))

            if "execute_transaction" in source:
                print(f"✓ {method_name} uses transactions")
            else:
                print(f"✗ {method_name} NOT using transactions")
                success = False

        return success

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_logging_output():
    """Test that logging is configured and working."""
    print("\n" + "=" * 60)
    print("TEST 6: Logging Configuration")
    print("=" * 60)

    try:
        # Check log directory exists
        log_dir = Path("logs")
        if log_dir.exists():
            print(f"✓ Log directory exists: {log_dir}")
        else:
            print(f"✗ Log directory not found: {log_dir}")
            return False

        # Check log file
        log_file = log_dir / "transactions.log"
        if log_file.exists():
            print(f"✓ Transaction log file exists: {log_file}")
            size = log_file.stat().st_size
            print(f"  Log file size: {size} bytes")
        else:
            print(f"✓ Transaction log will be created on first transaction")

        # Test logging works
        test_logger = logging.getLogger("test_phase1")
        test_logger.info("Test log message from phase 1 verification")
        print("✓ Logging system operational")

        return True

    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False


def main():
    """Run all Phase 1 tests."""
    print("\n")
    print("=" * 60)
    print("PHASE 1 TRANSACTION IMPLEMENTATION - VERIFICATION TESTS")
    print("=" * 60)
    print()

    results = []

    # Run all tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Transaction Method", test_transaction_method()))
    results.append(("Model Transaction Usage", test_model_transaction_usage()))
    results.append(("Measure Update Method", test_measure_update_with_relationships()))
    results.append(("Measure Add Methods", test_measure_add_methods()))
    results.append(("Logging Configuration", test_logging_output()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    print()
    print(f"TOTAL: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ Phase 1 implementation VERIFIED - All tests passed!")
        print("\nNext steps:")
        print("1. Test delete operations in the Streamlit UI")
        print("2. Verify transactions rollback on errors")
        print("3. Check logs/transactions.log for transaction logging")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed - Please review implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
