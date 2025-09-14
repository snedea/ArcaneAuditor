# Extend Reviewer Rules Breakdown

This document provides a comprehensive overview of all validation rules supported by the Extend Reviewer tool. These rules help catch code quality issues, style violations, and structural problems that compilers can't detect but are important for code reviewers to identify.

## Rule Categories

The rules are organized into three main categories:
- **Script Rules**: Code quality and best practices for PMD scripts
- **Structure Rules**: Structural validation and required field checks  
- **Style Rules**: Naming convention enforcement

---

## Script Rules

### ScriptVarUsageRule - Script Var Usage Rule
**Severity:** WARNING  
**Description:** Ensures scripts use 'let' or 'const' instead of 'var' (best practice)

**What it catches:**
- Usage of `var` declarations instead of modern `let`/`const`
- Variable declarations that don't follow Extend best practices

**Example violations:**
```javascript
var myVariable = "value";  // ❌ Should use 'let' or 'const'
```

**Fix:**
```javascript
const myVariable = "value";  // ✅ Use 'const' for immutable values
let myVariable = "value";    // ✅ Use 'let' for mutable values
```

---

### ScriptNestingLevelRule - Script Nesting Level Rule
**Severity:** WARNING  
**Description:** Ensures scripts don't have excessive nesting levels (max 4 levels)

**What it catches:**
- Overly nested code structures (if statements, loops, functions)
- Code that's difficult to read and maintain due to deep nesting

**Example violations:**
```javascript
function processData(data) {
    if (data) {                    // Level 1
        if (data.isValid) {        // Level 2
            if (data.hasContent) { // Level 3
                if (data.length > 0) { // Level 4
                    if (data.items) {  // ❌ Level 5 - Too deep!
                        return data.items.map(item => item.value);
                    }
                }
            }
        }
    }
}
```

**Fix:**
```javascript
// ✅ Use early returns to reduce nesting
function processData(data) {
    if (!data || !data.isValid || !data.hasContent) {
        return null;
    }
    
    if (data.length <= 0 || !data.items) {
        return null;
    }
    
    return data.items.map(item => item.value);
}
```

---

### ScriptComplexityRule - Script Complexity Rule
**Severity:** WARNING  
**Description:** Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)

**What it catches:**
- Functions with too many decision points (if, while, for, ternary operators)
- Complex code that's hard to test and maintain

**Example violations:**
```javascript
function calculateGrade(score, attendance, bonus) {
    let grade = 'F';
    
    if (score >= 90) grade = 'A';      // +1 complexity
    else if (score >= 80) grade = 'B'; // +1 complexity  
    else if (score >= 70) grade = 'C'; // +1 complexity
    else if (score >= 60) grade = 'D'; // +1 complexity
    
    if (attendance < 80) grade = 'F';  // +1 complexity
    if (bonus > 0) {                   // +1 complexity
        if (grade == 'A') grade = 'A+'; // +1 complexity
        else if (grade == 'B') grade = 'B+'; // +1 complexity
        else if (grade == 'C') grade = 'C+'; // +1 complexity
    }
    
    // Multiple ternary operators add complexity
    let status = grade == 'F' ? 'fail' : 'pass'; // +1 complexity
    let retake = grade == 'F' || grade == 'D' ? true : false; // +1 complexity
    
    return { "grade": grade, "status": status, "retake": retake }; // ❌ Total complexity: 10+ (too high!)
}
```

**Fix:**
```javascript
// ✅ Break into smaller, focused functions
function getBaseGrade(score) {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
}

function applyBonus(baseGrade, bonus) {
    if (bonus <= 0) return baseGrade;
    if (baseGrade == 'A') return 'A+';
    if (baseGrade == 'B') return 'B+';
    if (baseGrade == 'C') return 'C+';
    return baseGrade;
}

function calculateGrade(score, attendance, bonus) {
    let grade = getBaseGrade(score);
    
    if (attendance < 80) grade = 'F';
    else grade = applyBonus(grade, bonus);
    
    return {
        "grade": grade,
        "status": grade == 'F' ? 'fail' : 'pass',
        "retake": grade == 'F' || grade == 'D'
    };
}
```

---

### ScriptUnusedVariableRule - Script Unused Variable Rule
**Severity:** WARNING  
**Description:** Ensures all declared variables are used (prevents dead code) with proper scoping awareness

**What it catches:**
- Variables declared but never used
- Dead code that clutters the codebase
- Variables in different scopes (global vs function-level)

**Example violations:**
```javascript
let unusedVariable = "never used";  // ❌ Declared but never used
let anotherVar = "also unused";

function myFunction() {
    let localUnused = "not used here either";  // ❌ Local scope unused
    return "something";
}
```

**Fix:**
```javascript
// ✅ Remove unused variables
function myFunction() {
    return "something";
}
```

---

### ScriptConsoleLogRule - Script Console Log Rule
**Severity:** WARNING  
**Description:** Ensures scripts don't contain console statements (production code)

**What it catches:**
- Debug statements left in production code (console.debug, console.info, console.warn, console.error)
- Console logging that should be removed before deployment

**Example violations:**
```javascript
console.debug("Debug message");   // ❌ Debug statement
console.info("Info message");     // ❌ Debug statement
console.warn("Warning message");  // ❌ Debug statement
console.error("Error occurred");  // ❌ Debug statement
```

**Fix:**
```javascript
// ✅ Remove all console statements from production code
// Use proper logging mechanisms or remove entirely

// ✅ Commenting out console statements is also acceptable
// console.debug("Debug message");
// console.info("Info message");
// console.warn("Warning message");
// console.error("Error occurred");
```

---

### ScriptMagicNumberRule - Script Magic Number Rule
**Severity:** INFO  
**Description:** Ensures scripts don't contain magic numbers (use named constants)

**What it catches:**
- Hardcoded numeric values without explanation (magic numbers)
- Numbers that should be named constants for maintainability
- Values like `200`, `5000`, `3` that lack context and should be `HTTP_OK`, `DEFAULT_TIMEOUT`, `MAX_RETRIES`

**Example violations:**
```javascript
if (response.status == 200) {     // ❌ Magic number - hardcoded value
    let timeout = 5000;            // ❌ Magic number - should be a named constant
    let maxRetries = 3;            // ❌ Magic number - should be a named constant
    
    // More magic numbers in calculations
    let retryDelay = timeout * 2;  // ❌ Magic number '2'
    if (attempts > 5) {            // ❌ Magic number '5'
        return false;
    }
}
```

**Fix:**
```javascript
// ✅ Define named constants for all magic numbers
const httpOk = 200;               // ✅ Named constant
const defaultTimeout = 5000;      // ✅ Named constant
const maxRetryAttempts = 3;       // ✅ Named constant
const retryMultiplier = 2;        // ✅ Named constant
const maxAttempts = 5;            // ✅ Named constant

if (response.status == httpOk) {
    let timeout = defaultTimeout;
    let maxRetries = maxRetryAttempts;
    
    // ✅ Use named constants instead of magic numbers
    let retryDelay = timeout * retryMultiplier;
    if (attempts > maxAttempts) {
        return false;
    }
}
```

---

### ScriptLongFunctionRule - Script Long Function Rule
**Severity:** WARNING  
**Description:** Ensures functions don't exceed maximum line count (max 50 lines)

**What it catches:**
- Functions that are too long and difficult to understand
- Functions that do too many things (violating single responsibility)

**Example violations:**
```javascript
function longFunction() {
    // 60+ lines of code...  // ❌ Too long
    // Multiple responsibilities
    // Hard to test and maintain
}
```

**Fix:**
```javascript
// ✅ Break into smaller, focused functions
function validateInput(data) {
    // validation logic
}

function processData(data) {
    // processing logic
}

function formatOutput(data) {
    // formatting logic
}

function mainFunction(input) {
    validateInput(input);
    const processed = processData(input);
    return formatOutput(processed);
}
```

---

### ScriptVariableNamingRule - Script Variable Naming Rule
**Severity:** WARNING  
**Description:** Ensures variables follow lowerCamelCase naming convention

**What it catches:**
- Variables that don't follow the project's camelCase convention
- Inconsistent naming that affects code readability

**Example violations:**
```javascript
let snake_case_var = "value";    // ❌ Snake case
let PascalCase = "value";        // ❌ Pascal case
let UPPER_CASE = "value";        // ❌ Upper case
```

**Fix:**
```javascript
let snakeCaseVar = "value";      // ✅ Lower camel case
let pascalCase = "value";        // ✅ Lower camel case
let upperCase = "value";         // ✅ Lower camel case
```

---

### EndpointOnSendSelfDataRule - Endpoint On Send Self Data Rule
**Severity:** WARNING  
**Description:** Ensures endpoints don't use anti-pattern 'self.data = {:}' in onSend scripts

**What it catches:**
- Using `self.data = {:}` to assign a new empty map (anti-pattern)
- Should create a separate variable like `payload` instead

**Example violations:**
```javascript
// In endpoint onSend script
self.data = {:}  // ❌ Anti-pattern
```

**Fix:**
```javascript
// ✅ Create a separate variable for the data map
let payload = {:};

// ✅ Use the separate variable for processing
payload["key1"] = "value1";
payload["key2"] = "value2";

// ✅ Return the data instead of assigning to self.data
return payload;
```

---

### ScriptNullSafetyRule - Script Null Safety Rule
**Severity:** WARNING  
**Description:** Ensures property access chains are protected against null reference exceptions

**What it catches:**
- Unsafe property access that could cause null reference errors
- Missing null checks in property chains
- Should use `empty` checks or null coalescing operator (`??`)

**Example violations:**
```javascript
let result = obj.prop.subProp.value;  // ❌ Unsafe - could throw if obj.prop is null
let data = user.profile.name;         // ❌ Unsafe - could throw if user.profile is null
```

**Fix:**
```javascript
// ✅ Use empty checks
if (!empty obj.prop.subProp) {
    let result = obj.prop.subProp.value;
}

// ✅ Use null coalescing operator
let result = obj.prop?.subProp?.value ?? "defaultValue";
let data = user.profile?.name ?? "unknown";

// ✅ Chain operator (helps indicate when an object or prop can be null)
let result = obj?.prop?.subProp?.value;
let data = user?.profile?.name;
```

---

### ScriptVerboseBooleanCheckRule - Script Verbose Boolean Check Rule
**Severity:** WARNING  
**Description:** Ensures scripts don't use overly verbose boolean checks (if(var == true) return true else return false)

**What it catches:**
- Redundant boolean comparisons and returns
- Overly verbose conditional logic

**Example violations:**
```javascript
if (isValid == true) {
    return true;
} else {
    return false;
}  // ❌ Verbose - can be simplified

let result = isValid == true ? true : false;  // ❌ Verbose ternary
```

**Fix:**
```javascript
return isValid;  // ✅ Simple and clear

let result = isValid;  // ✅ Simple assignment

// ✅ Simple boolean check without comparison
if (isValid) {
    // do something when true
} else {
    // do something when false
}
```

---

## Structure Rules

### WidgetIdRequiredRule - Widget ID Required Rule
**Severity:** WARNING  
**Description:** Ensures all widgets have an 'id' field set (structure validation)

**What it catches:**
- Widgets missing required 'id' fields
- Structural issues that could affect functionality

**Example violations:**
```json
{
  "type": "text",
  "value": "Hello World"
  // ❌ Missing 'id' field
}
```

**Fix:**
```json
{
  "type": "text",
  "id": "welcomeText",        // ✅ Required 'id' field
  "value": "Hello World"
}
```

---

### FooterPodRequiredRule - Footer Pod Required Rule
**Severity:** WARNING  
**Description:** Ensures footer uses pod structure (direct pod or footer with pod children)

**What it catches:**
- Footers that don't use the required pod structure
- Structural violations in footer implementation

**Example violations:**
```json
{
  "footer": {
    "type": "footer",
    "children": [
      {
        "type": "text",  // ❌ Should be 'pod' type
        "value": "Footer content"
      }
    ]
  }
}
```

**Fix:**
```json
{
  "footer": {
    "type": "pod",  // ✅ Direct pod structure
    "podId": "footer"
  }
}

// OR

{
  "footer": {
    "type": "footer",
    "children": [
      {
        "type": "pod",  // ✅ Footer with pod children
        "podId": "footer"
      }
    ]
  }
}
```

---

### EndpointFailOnStatusCodesRule - Endpoint Fail On Status Codes Rule
**Severity:** WARNING  
**Description:** Ensures endpoints have failOnStatusCodes with minimum required codes 400 and 403

**What it catches:**
- Missing failOnStatusCodes configuration
- Incomplete error handling setup

**Example violations:**
```json
{
  "name": "myEndpoint",
  "url": "https://api.example.com/data"
  // ❌ Missing failOnStatusCodes
}
```

**Fix:**
```json
{
  "name": "myEndpoint",
  "url": "https://api.example.com/data",
  "failOnStatusCodes": [    // ✅ Required to catch 400 and 403 errors
    { "code": "400" },
    { "code": "403" }
  ]
}
```

---

### StringBooleanRule - String Boolean Rule
**Severity:** WARNING  
**Description:** Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans

**What it catches:**
- String representations of boolean values instead of actual booleans
- Type inconsistencies that could cause logic errors

**Example violations:**
```json
{
  "enabled": "true",     // ❌ String instead of boolean
  "visible": "false"     // ❌ String instead of boolean
}
```

**Fix:**
```json
{
  "enabled": true,       // ✅ Actual boolean
  "visible": false       // ✅ Actual boolean
}
```

---

### EndpointUrlBaseUrlTypeRule - Endpoint URL Base URL Type Rule
**Severity:** WARNING  
**Description:** Ensures endpoint URLs don't include hardcoded workday.com or apiGatewayEndpoint values

**What it catches:**
- Hardcoded URLs that should use baseUrlType configuration
- URLs that aren't environment-agnostic

**Example violations:**
```json
{
  "name": "myEndpoint",
  "url": "https://api.workday.com/v1/wql"  // ❌ Hardcoded workday.com
}
```

**Fix:**
```json
{
  "name": "GetCurrentWorker",
  "url": "workers/me",               // ✅ Relative URL
  "baseUrlType": "workday-common"    // ✅ Use baseUrlType
}
```

---

## Style Rules

### WidgetIdLowerCamelCaseRule - Widget ID Lower Camel Case Rule
**Severity:** WARNING  
**Description:** Ensures widget IDs follow lowerCamelCase naming convention (style guide)

**What it catches:**
- Widget IDs that don't follow the project's camelCase convention
- Inconsistent naming that affects code style

**Example violations:**
```json
{
  "type": "text",
  "id": "my_widget_id",     // ❌ Snake case
  "value": "Hello"
}
```

**Fix:**
```json
{
  "type": "text",
  "id": "myWidgetId",       // ✅ Lower camel case
  "value": "Hello"
}
```

---

### EndpointNameLowerCamelCaseRule - Endpoint Name Lower Camel Case Rule
**Severity:** WARNING  
**Description:** Ensures endpoint names follow lowerCamelCase naming convention (style guide)

**What it catches:**
- Endpoint names that don't follow the project's camelCase convention
- Inconsistent API naming

**Example violations:**
```json
{
  "name": "GetCurrentWorker",    // ❌ Pascal case
  "url": "workers/me",
  "baseUrlType": "workday-common"
}
```

**Fix:**
```json
{
  "name": "getCurrentWorker",    // ✅ Lower camel case
  "url": "workers/me",
  "baseUrlType": "workday-common"
}
```

---

## Summary

The Extend Reviewer tool provides **24 comprehensive validation rules** across three categories:

- **16 Script Rules** - Code quality, best practices, and maintainability
- **6 Structure Rules** - Required fields, proper configuration, and structural validation  
- **2 Style Rules** - Naming convention enforcement

These rules help ensure:
- ✅ **Code Quality** - Modern JavaScript practices, complexity management
- ✅ **Maintainability** - Clear naming, appropriate function sizes, reduced nesting
- ✅ **Reliability** - Null safety, proper error handling, required configurations
- ✅ **Consistency** - Uniform naming conventions across the codebase
- ✅ **Production Readiness** - No debug statements, proper boolean types

All rules are designed to catch issues that compilers can't detect but are crucial for code reviewers to identify and address.
