# Section 1.3 Verification Tests - Atomic Measure Updates

This document contains 5 manual tests to verify that section 1.3 of the TRANSACTION_DEPLOYMENT_PLAN.md is complete and working correctly.

## Overview

Section 1.3 implements atomic measure updates with relationships. The `update_with_relationships()` method executes:
- 1 UPDATE (measure data)
- 3 DELETEs (old relationships)
- N INSERTs (new relationships)

All in a single atomic transaction - either all succeed or all roll back.

---

## Test 1: Basic Measure Update with Relationship Changes

**Purpose:** Verify that updating a measure and changing its relationships works atomically.

**Steps:**
1. Open the Measures page in the Streamlit app
2. Select an existing measure (note its current name, types, stakeholders, and benefits)
3. Update the measure:
   - Change the measure name
   - Remove at least one existing measure type and add a different one
   - Remove at least one stakeholder and add a different one
   - Change at least one benefit
4. Submit the update
5. Verify the measure was updated with the new name
6. Verify ALL old relationships are gone and ALL new relationships are present

**Expected Result:** ✅ All changes applied in a single atomic operation - no partial states

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
Measure ID tested:
Old relationships:
New relationships:
Result:
```

---

## Test 2: Clear All Relationships (Empty Lists)

**Purpose:** Verify that removing all relationships works correctly.

**Steps:**
1. Select a measure that has types, stakeholders, and benefits
2. Update the measure to clear all relationships:
   - Unselect all measure types (empty list)
   - Unselect all stakeholders (empty list)
   - Unselect all benefits (empty list)
3. Submit the update
4. Verify all relationships were removed

**Expected Result:** ✅ Measure exists but has no types, stakeholders, or benefits

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
Measure ID tested:
Before: X types, Y stakeholders, Z benefits
After: 0 types, 0 stakeholders, 0 benefits
Result:
```

---

## Test 3: Update Only Measure Data (No Relationship Changes)

**Purpose:** Verify updates work when only changing measure fields, not relationships.

**Steps:**
1. Select a measure
2. Change only the measure description or status (don't touch relationships)
3. Submit the update
4. Verify the measure data changed
5. Verify all existing relationships remained unchanged

**Expected Result:** ✅ Measure data updated, relationships untouched

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
Measure ID tested:
Field changed:
Relationships before:
Relationships after:
Result:
```

---

## Test 4: Transaction Logging Verification

**Purpose:** Verify that the update is logged as a single transaction.

**Steps:**
1. Open a terminal and tail the transaction log:
   ```bash
   tail -f logs/transactions.log
   ```
2. In the app, update a measure with relationship changes
3. Check the log output

**Expected Result:** ✅ Log shows:
- Single transaction start message
- Multiple operations within the transaction (UPDATE + DELETEs + INSERTs)
- Single "transaction committed successfully" message
- No separate commit messages for each operation

**Status:** [ ] Pass / [ ] Fail

**Log Output:**
```
Paste relevant log entries here:




```

---

## Test 5: Atomicity Under Error Conditions (Rollback Test)

**Purpose:** Verify that if the update fails, everything rolls back (no partial changes).

**Steps:**
1. Note the current state of a measure (name + all relationships)
2. Attempt an update that might fail:
   - Try updating with invalid data (if validation allows you to submit)
   - Or check the logs during a normal update to see transaction handling
3. If the update fails, verify the measure is unchanged
4. If the update succeeds, check logs show atomic transaction

**Expected Result:** ✅ Either:
- Update succeeds completely (all-or-nothing), OR
- Update fails completely and measure remains in original state (rollback worked)
- Log shows either "transaction committed" or "transaction rolled back"

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
Measure ID tested:
State before update:
Update attempted:
State after update:
Transaction result (committed/rolled back):
```

---

## Quick Verification Checklist

After running these tests, verify:
- [ ] Updates are processed as single transactions (check logs)
- [ ] Relationship changes are atomic (all succeed or all fail)
- [ ] No orphaned relationships left behind
- [ ] UI shows single success/error message (not multiple messages)
- [ ] Log file shows transaction begin → operations → commit pattern

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Basic Update with Relationships | [ ] Pass / [ ] Fail | |
| Test 2: Clear All Relationships | [ ] Pass / [ ] Fail | |
| Test 3: Update Measure Data Only | [ ] Pass / [ ] Fail | |
| Test 4: Transaction Logging | [ ] Pass / [ ] Fail | |
| Test 5: Atomicity/Rollback | [ ] Pass / [ ] Fail | |

**Overall Section 1.3 Status:** [ ] Complete / [ ] Issues Found

**Date Tested:** _____________

**Tested By:** _____________

---

## Issues Found (if any)

```
Document any issues discovered during testing:




```

---

## Sign-Off

**Section 1.3 (Atomic Measure Updates) is:**
- [ ] VERIFIED and ready for Phase 2
- [ ] NEEDS REVISION (see issues above)

**Next Steps:**
- [ ] Proceed to Phase 2 (Backup Infrastructure)
- [ ] Address issues found in testing
