#!/usr/bin/env python3
"""Validation script for Fulcrum improvements system.

Emits test operations to verify the improvements client is working correctly.
Useful for testing environment setup and improvements API connectivity.

Usage:
    # Set required environment variables first
    export FULCRUM_IMPROVEMENTS_URL="http://localhost:8000/api/improvements"
    export FULCRUM_RUN_TOKEN="test-token"
    export FULCRUM_RUN_UUID="test-run-uuid"

    # Run the script
    uv run skills/fulcrum-sdk/scripts/improvements.py
"""

from fulcrum_sdk._internal.improvements import get_improvements_client


def main() -> None:
    """Run improvements validation tests."""
    improvements = get_improvements_client()

    print("Fulcrum Improvements Validation")
    print("=" * 40)

    if not improvements.enabled:
        print("ERROR: Improvements client is not enabled.")
        print("\nRequired environment variables:")
        print("  - FULCRUM_IMPROVEMENTS_URL")
        print("  - FULCRUM_RUN_TOKEN (or FULCRUM_DISPATCH_TOKEN)")
        print("  - FULCRUM_RUN_UUID")
        print("\nSet these variables and try again.")
        return

    print("Client enabled: YES")
    print()

    # Test 1: List improvements
    print("Test 1: list_improvements")
    result = improvements.list_improvements()
    print(f"  Result: Found {len(result)} improvements")

    # Test 2: Create improvement
    print("Test 2: create_improvement")
    result = improvements.create_improvement(
        title="Validation test improvement",
        description="Created by improvements validation script",
        dedupe_key="validation-test-001",
        status="open",
    )
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")

    # Test 3: List again to verify creation
    print("Test 3: list_improvements (verify creation)")
    result = improvements.list_improvements()
    test_improvement = next(
        (i for i in result if i.dedupe_key == "validation-test-001"), None
    )
    if test_improvement:
        print(f"  Result: Found created improvement (uuid: {test_improvement.uuid})")

        # Test 4: Update improvement
        print("Test 4: update_improvement")
        update_result = improvements.update_improvement(
            test_improvement.uuid, status="resolved"
        )
        print(f"  Result: {'SUCCESS' if update_result else 'FAILED'}")

        # Test 5: Emit event
        print("Test 5: emit_improvement_event")
        event_result = improvements.emit_improvement_event(
            test_improvement.uuid,
            action="validated",
            payload={"test_mode": True},
        )
        print(f"  Result: {'SUCCESS' if event_result else 'FAILED'}")

        # Test 6: Delete improvement
        print("Test 6: delete_improvement")
        delete_result = improvements.delete_improvement(test_improvement.uuid)
        print(f"  Result: {'SUCCESS' if delete_result else 'FAILED'}")
    else:
        print("  Result: Could not find created improvement (API may not support list)")
        print("  Skipping update, event, and delete tests")

    print()
    print("Validation complete.")


if __name__ == "__main__":
    main()
