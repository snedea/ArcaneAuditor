# Extend Reviewer - Additional Rule Ideas

This document tracks potential new validation rules that could be added to the Extend Reviewer tool to enhance PMD Script validation and code quality.

## Additional Script Rules


---

### Duplicate Code Rule
**Severity:** WARNING  
**Description:** Ensures scripts don't contain duplicate code blocks (DRY principle)

**What it catches:**
- Repeated code blocks that should be extracted into functions
- Code that violates the Don't Repeat Yourself principle

**Example violations:**
```javascript
if (user.role == "admin") {
    let permissions = ["read", "write", "delete"];
    let hasAccess = checkPermissions(permissions);
} else if (user.role == "manager") {
    let permissions = ["read", "write"];  // ❌ Duplicate permission logic
    let hasAccess = checkPermissions(permissions);
}
```

**Fix:**
```javascript
let rolePermissions = {
    "admin": ["read", "write", "delete"],
    "manager": ["read", "write"]
};
let permissions = rolePermissions[user.role];
let hasAccess = checkPermissions(permissions);
```

---

### String Concatenation Rule
**Severity:** WARNING  
**Description:** Ensures scripts use template literals instead of string concatenation

**What it catches:**
- String concatenation using `+` operator
- Code that should use template literals for better readability

**Example violations:**
```javascript
let message = "Hello " + userName + ", you have " + count + " items";  // ❌ String concatenation
```

**Fix:**
```javascript
let message = `Hello {{userName}}, you have {{count}} items`;  // ✅ Template literal
```

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

### Functional Method Usage Rule
**Severity:** WARNING  
**Description:** Ensures scripts use appropriate functional methods instead of manual loops

**What it catches:**
- Manual loops that could be replaced with functional methods
- Code that should use `forEach`, `map`, `filter`, etc.

**Example violations:**
```javascript
let doubled = [];
for (let i = 0; i < numbers.length; i++) {  // ❌ Manual loop
    doubled.push(numbers[i] * 2);
}
```

**Fix:**
```javascript
let doubled = numbers.map(num => num * 2);  // ✅ functional method
```

---

## Implementation Priority

### High Priority
- Unused Function Parameters (easy to implement)
- Empty Function (easy to implement)
- Function Return Consistency (moderate complexity)

### Medium Priority
- Function Complexity (parameter counting)
- String Concatenation (pattern matching)
- Variable Declaration Scope (AST analysis)

### Lower Priority
- Duplicate Code (complex AST comparison)
- Array Method Usage (complex pattern matching)
- Function Length (simple but low impact)
- Comment Quality (subjective, complex to implement)

## Notes

- All examples use PMD Script syntax (loose equality `==`, camelCase naming, etc.)
- Rules should follow the existing pattern in `parser/rules/script_validation_rules.py`
- Consider adding configuration options for thresholds (max parameters, max function length, etc.)
- Some rules may require AST analysis capabilities beyond current grammar
