# ADR Category Persistence Fix — Session Report

**Date:** 2026-03-01 → 2026-03-03  
**Commits:** `b0202f1`, `c56e6f1`, `067b10f`, `71669b0`, `bf50e59`  
**Status:** ✅ RESOLVED

---

## Problem Statement

Η κατηγορία ADR (Επικίνδυνα Εμπορεύματα) επιλεγόταν από το dropdown στη φόρμα συμμόρφωσης οδηγού, αλλά **ΔΕΝ αποθηκευόταν στη βάση δεδομένων**. Όταν ο χρήστης ξανάνοιγε τη φόρμα, το dropdown ήταν κενό.

### User Report
```
"Όταν άλλαξα την κατηγορία από Π3 σε Π4 και πάτησα Ενημέρωση, 
η φόρμα επέστρεψε χωρίς να δείχνει την επιλεγμένη κατηγορία."
```

### Observed Behavior
- **Frontend:** Dropdown επιτρέπει επιλογή ADR category (Π1-Π9)
- **Form Validation:** `cleaned_data` περιέχει `adr_category: <AdrCategory: Π5>`
- **Database:** `adr_categories` ManyToMany relation είναι **κενό** (`[]`)
- **Form Reload:** Dropdown δείχνει "— Χωρίς ADR —" αντί για την επιλεγμένη κατηγορία

---

## Investigation Process

### Step 1: Initial Hypothesis (WRONG)
**Υπόθεση:** Το `initial` value δεν γινόταν σωστά populate στη φόρμα.

**Δοκιμή:**
```python
# web/forms.py - DriverComplianceForm.__init__()
if instance and instance.pk:
    first_adr = instance.adr_categories.first()
    if first_adr:
        self.fields["adr_category"].initial = first_adr.pk
        self.initial["adr_category"] = first_adr.pk
```

**Αποτέλεσμα:** ❌ Δεν λύθηκε το πρόβλημα

---

### Step 2: Database Verification
**Εντολή:**
```python
from core.driver_compliance_models import DriverCompliance
c = DriverCompliance.objects.prefetch_related('adr_categories').get(employee_id=4)
print(f"ADR Categories in DB: {list(c.adr_categories.all())}")
# Output: ADR Categories in DB: []
```

**Εύρημα:** Η βάση είναι **κενή**. Το πρόβλημα δεν είναι στο display, αλλά στο **save**.

---

### Step 3: Form Save Logic Analysis
**Logs:**
```
[DRIVER_COMPLIANCE_SAVE] Form is valid. Cleaned data: {..., 'adr_category': <AdrCategory: Π5>}
[ADR_SAVE] Setting adr_categories to [Π5]
[ADR_SAVE] After set, count: 1
[DRIVER_COMPLIANCE_SAVE] ADR categories count after save_m2m: 0  ← PROBLEM!
```

**Εύρημα:** Το `M2M.set()` καλείται και δείχνει count: 1, αλλά μετά το `save_m2m()` το count είναι 0!

---

### Step 4: save_m2m() Override Investigation
**Υπόθεση:** Το `save_m2m()` override στο `DriverComplianceForm` δεν εκτελείται.

**Δοκιμή:** Προσθήκη logging στο `save_m2m()`:
```python
def save_m2m(self):
    logger.info(f"[SAVE_M2M] Called. Instance pk: {self.instance.pk}")
    super().save_m2m()
    self._apply_adr_single_select(self.instance)
    logger.info(f"[SAVE_M2M] ADR count after: {self.instance.adr_categories.count()}")
```

**Αποτέλεσμα:** ❌ **ΔΕΝ υπάρχουν [SAVE_M2M] logs!** Η μέθοδος δεν καλείται ποτέ.

---

### Step 5: Root Cause Identification

**Ανάλυση του View:**
```python
# web/views.py - driver_compliance_save()
obj = form.save(commit=False)  # Καλεί save() που κάνει _apply_adr_single_select()
obj.employee = employee
obj.save()  # Σώζει το instance
form.save_m2m()  # Καλεί το parent save_m2m(), ΟΧΙ το override!
```

**Root Cause:**
1. Το `form.save(commit=False)` καλεί το `DriverComplianceForm.save()`
2. Το `save()` καλεί `_apply_adr_single_select()` που κάνει `instance.adr_categories.set([adr_category])`
3. Αυτό δείχνει count: 1 **στη μνήμη**, αλλά δεν γράφεται στη βάση
4. Το `form.save_m2m()` καλεί το **parent class** `save_m2m()`, ΟΧΙ το override του `DriverComplianceForm`
5. Το parent `save_m2m()` σώζει τα `license_categories` αλλά ΔΕΝ καλεί το `_apply_adr_single_select()`
6. Αποτέλεσμα: Το ADR χάνεται

**Γιατί το override δεν καλείται;**
- Το `DriverComplianceForm` κληρονομεί από `TailwindFormMixin` και `forms.ModelForm`
- Το MRO (Method Resolution Order) μπορεί να προκαλεί το parent `save_m2m()` να καλείται αντί του override
- Ή το `save_m2m()` δεν καλείται καθόλου λόγω του `commit=False` pattern

---

## Solution

### Final Fix: Move ADR Save Logic to View

**Αλλαγές στο `web/forms.py`:**
```python
def save(self, commit=True):
    """
    Σώζει το instance.
    CRITICAL: Do NOT call _apply_adr_single_select here!
    It will be called by save_m2m() which is the proper place for M2M operations.
    """
    instance = super().save(commit=commit)
    return instance
```

**Αλλαγές στο `web/views.py`:**
```python
# driver_compliance_save view
obj = form.save(commit=False)
obj.employee = employee
obj.save()

# Save ManyToMany relations (license_categories)
form.save_m2m()

# CRITICAL FIX: Manually handle ADR single-select
adr_category = form.cleaned_data.get("adr_category")
if adr_category:
    obj.adr_categories.set([adr_category])
else:
    obj.adr_categories.clear()
```

**Αλλαγές στο `web/views.py` (driver_compliance_form):**
```python
# Prefetch M2M relations for form initial values
compliance = DriverCompliance.objects.prefetch_related(
    'license_categories',
    'adr_categories'
).get(employee=employee)
```

---

## Verification

### Before Fix
```bash
$ python check_adr.py
Employee: Γιάννης Παραγιός
ADR Categories in DB: []
Total ADR categories: 0
```

### After Fix
```bash
$ python check_adr.py
Employee: Γιάννης Παραγιός
ADR Categories in DB: [<AdrCategory: Π5 - Βασική + Βυτία>]
Total ADR categories: 1
```

### Logs After Fix
```
[DRIVER_COMPLIANCE_SAVE] Form is valid. Cleaned data: {..., 'adr_category': <AdrCategory: Π5>}
[DRIVER_COMPLIANCE_SAVE] Before calling form.save_m2m()
[DRIVER_COMPLIANCE_SAVE] After calling form.save_m2m()
[DRIVER_COMPLIANCE_SAVE] Manually setting ADR to: Π5 - Βασική + Βυτία
[DRIVER_COMPLIANCE_SAVE] ADR set complete. Count: 1
[DRIVER_COMPLIANCE_SAVE] Final ADR categories count: 1
```

---

## Key Learnings

### 1. Django Form save_m2m() Override Pitfalls
- Το `save_m2m()` override μπορεί να μην καλείται αν υπάρχει complex MRO
- Το `commit=False` pattern απαιτεί προσοχή με M2M relations
- Καλύτερη πρακτική: Χειρισμός M2M **μετά** το `form.save_m2m()` στο view

### 2. ManyToMany Relations & Transactions
- Το `M2M.set()` μέσα στο `save()` method δεν γράφεται στη βάση αν το instance δεν έχει committed
- Το `M2M.set()` πρέπει να γίνεται **μετά** το `instance.save()` ΚΑΙ **μετά** το `form.save_m2m()`

### 3. Debugging Strategy
- Extensive logging σε κάθε βήμα (save, save_m2m, _apply_adr_single_select)
- Database verification με standalone script
- Logs comparison: memory count vs database count

### 4. ADR Business Logic
- Ένας οδηγός μπορεί να έχει **μόνο μία** κατηγορία ADR (Π1-Π9)
- Κάθε κατηγορία είναι ιεραρχική και ενσωματώνει τις προηγούμενες
- Π9 (πλήρης ADR) ενσωματώνει όλες τις άλλες

---

## Files Changed

### web/forms.py
- Simplified `DriverComplianceForm.save()` to just call `super().save()`
- Kept `save_m2m()` override with logging (for future debugging)
- Kept `_apply_adr_single_select()` method (unused now, but kept for tests compatibility)

### web/views.py
- `driver_compliance_save`: Added manual ADR save after `form.save_m2m()`
- `driver_compliance_form`: Added `prefetch_related('adr_categories')` for proper initial value loading

### web/templates/partials/driver_compliance_modal.html
- ADR section με single-select dropdown
- Proper field rendering με Tailwind CSS

### tests/test_driver_compliance_ui.py
- UI regression tests για driver compliance modal

### core/migrations/0012_fix_adr_categories.py
- Migration για ADR data cleanup (if needed)

---

## Testing Checklist

- [x] ADR category saves to database
- [x] ADR category displays when reopening form
- [x] ADR category can be changed (Π3 → Π4 → Π5)
- [x] ADR category can be cleared (select "— Χωρίς ADR —")
- [x] License categories still work (multi-select)
- [x] PEI fields still work
- [x] Tachograph fields still work
- [x] Form validation still works (9-digit license, 16-char tachograph)
- [x] TransportOrder hard-block validation still works

---

## Commits

1. **bf50e59** - "Fix: ADR category not displaying after save in DriverComplianceForm"
   - Initial attempt: Added explicit import, double initial setting

2. **067b10f** - "Fix: Reload DriverCompliance instance with prefetch_related to populate ADR category"
   - Attempted to reload instance from DB in form __init__

3. **71669b0** - "Add driver compliance UI and related changes"
   - Added modal template, UI tests, migration, URLs, views

4. **c56e6f1** - "Fix: Prefetch M2M relations in driver_compliance_form view"
   - Added prefetch_related in view to load M2M before passing to form

5. **b0202f1** - "Fix: ADR category now saves and displays correctly" ✅ FINAL FIX
   - Moved ADR save logic to view (manual set after form.save_m2m())
   - Simplified form save() method
   - Added extensive logging for debugging

---

## Conclusion

Το πρόβλημα λύθηκε με τη μεταφορά της λογικής αποθήκευσης ADR από τη φόρμα στο view. Αυτή η προσέγγιση είναι πιο explicit και αποφεύγει τα pitfalls του Django form `save_m2m()` override pattern.

**Lesson Learned:** Όταν έχεις custom M2M logic που δεν λειτουργεί με form overrides, μετέφερέ την στο view για πλήρη έλεγχο του save sequence.
