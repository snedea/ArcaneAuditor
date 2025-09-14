# Extend Reviewer - Additional Rule Ideas

This document tracks potential new validation rules that could be added to the Extend Reviewer tool to enhance PMD Script validation and code quality.

## Additional Script Rules

---

### Empty Function Rule
**Severity:** WARNING  
**Description:** Ensures functions have actual implementation (not empty bodies)

**What it catches:**
- Empty function bodies that indicate incomplete code
- Placeholder functions that were never implemented

**Example violations:**
```javascript
function calculateTotal(items) {  // ❌ Empty function body
    // TODO: implement this
}
```

**Fix:**
```javascript
function calculateTotal(items) {  // ✅ Implement the function
    let total = 0;
    for (let item : items) {
        total += item.price;
    }
    return total;
}
```

---

### Function Return Consistency Rule
**Severity:** WARNING  
**Description:** Ensures functions consistently return values (all paths return or none return)

**What it catches:**
- Functions with mixed return patterns (some paths return, others don't)
- Inconsistent function behavior that can cause bugs

**Example violations:**
```javascript
function processData(data) {
    if (data.isValid) {
        return data.value;  // ❌ Some paths return
    }
    // ❌ This path doesn't return anything
}
```

**Fix:**
```javascript
function processData(data) {  // ✅ All paths return
    if (data.isValid) {
        return data.value;
    }
    return null;
}
```

---

### Variable Declaration Scope Rule
**Severity:** WARNING  
**Description:** Ensures variables are declared in appropriate scopes (avoid global pollution)

**What it catches:**
- Variables declared at global scope that should be local
- Missing `let`/`const` declarations
- Variables that could cause scope conflicts

**Example violations:**
```javascript
// ❌ Global variable declaration
userName = "admin";

function processUser() {
    // ❌ Should use let/const
    userName = "user";
}
```

**Fix:**
```javascript
// ✅ Proper scope management
function processUser() {
    let userName = "user";  // Local scope
}
```

---

### Array Method Usage Rule
**Severity:** WARNING  
**Description:** Ensures appropriate use of array methods for common operations

**What it catches:**
- Manual array operations that could use built-in methods
- Inefficient array manipulation patterns

**Example violations:**
```javascript
// ❌ Manual array filtering
let validItems = [];
for (let i = 0; i < items.length; i++) {
    if (items[i].isValid) {
        validItems.push(items[i]);
    }
}
```

**Fix:**
```javascript
// ✅ Use built-in filter method
let validItems = items.filter(item => item.isValid);
```

---

### Function Length Rule
**Severity:** WARNING  
**Description:** Ensures functions don't exceed reasonable length limits

**What it catches:**
- Functions that are too long and should be broken down
- Functions that violate single responsibility principle

**Example violations:**
```javascript
function processOrder(order) {  // ❌ Too long (50+ lines)
    // ... lots of logic for validation
    // ... lots of logic for calculation  
    // ... lots of logic for formatting
    // ... lots of logic for sending
}
```

**Fix:**
```javascript
function processOrder(order) {  // ✅ Broken into smaller functions
    validateOrder(order);
    let total = calculateTotal(order);
    let formatted = formatOrder(order, total);
    sendOrder(formatted);
}
```

---

### Comment Quality Rule
**Severity:** INFO  
**Description:** Ensures functions have appropriate documentation

**What it catches:**
- Complex functions without comments
- Functions with unclear purpose
- Missing parameter documentation

**Example violations:**
```javascript
function calculateTax(amount, rate, discount) {  // ❌ No documentation
    let base = amount * rate;
    let adjusted = base - discount;
    return adjusted > 0 ? adjusted : 0;
}
```

**Fix:**
```javascript
/**
 * Calculates tax amount with optional discount
 * @param {number} amount - Base amount to tax
 * @param {number} rate - Tax rate (0.0 to 1.0)
 * @param {number} discount - Discount amount to apply
 * @returns {number} Final tax amount (minimum 0)
 */
function calculateTax(amount, rate, discount) {  // ✅ Well documented
    let base = amount * rate;
    let adjusted = base - discount;
    return adjusted > 0 ? adjusted : 0;
}
```

---

## Implementation Priority

### High Priority
- Empty Function (easy to implement)
- Function Return Consistency (moderate complexity)

### Medium Priority
- Variable Declaration Scope (AST analysis)
- Function Length (simple but moderate impact)

### Lower Priority
- Array Method Usage (complex pattern matching)
- Comment Quality (subjective, complex to implement)

## Notes

- All examples use PMD Script syntax (loose equality `==`, camelCase naming, etc.)
- Rules should follow the existing pattern in `parser/rules/script/`
- Consider adding configuration options for thresholds (max function length, etc.)
- Some rules may require AST analysis capabilities beyond current grammar

## Recently Implemented Rules

The following rules have been implemented and are no longer in the ideas list:

✅ **String Concatenation Rule** - Detects `+` usage for strings, recommends template literals  
✅ **Functional Method Usage Rule** - Detects manual loops that could use functional methods  
✅ **Function Complexity (Parameter Counting)** - Limits number of function parameters  
✅ **Magic Numbers Rule** - Detects hardcoded numbers that should be constants  
✅ **Null Safety Rule** - Detects unsafe property access chains  
✅ **Verbose Boolean Rule** - Detects verbose boolean expressions  
✅ **Console Log Rule** - Detects console.log usage in production code  
✅ **Variable Usage Rule** - Detects unused variables and parameters  
✅ **Variable Naming Rule** - Enforces camelCase naming conventions  
✅ **Unused Functions Rule** - Detects functions that are declared but never called  
✅ **Arrow Function Support** - Grammar support for `=>` syntax  
✅ **For...in Loop Support** - Grammar support for `for(let item : collection)`  
✅ **Range Operator Support** - Grammar support for `(0 to 100)` ranges  
✅ **Template Literal Support** - Grammar support for backticks and `{{ }}` syntax  
✅ **Namespace Syntax Support** - Grammar support for `module:function` calls
