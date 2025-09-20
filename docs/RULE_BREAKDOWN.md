# Arcane Auditor Rules Grimoire 📜

*Ancient wisdom distilled into 29 mystical validation rules*

This grimoire provides a comprehensive overview of all **29 validation rules** wielded by the Arcane Auditor. These enchantments help reveal hidden code quality issues, style violations, and structural problems that compilers cannot detect but are essential for master code wizards to identify. These rules help catch code quality issues, style violations, and structural problems that compilers can't detect but are important for code reviewers to identify.

## Rule Categories

The rules are organized into four main categories:

- **Script Rules (20 Rules)**: Code quality and best practices for PMD scripts and standalone script files
- **Endpoint Rules (4 Rules)**: API endpoint validation and compliance
- **Structure Rules (4 Rules)**: Widget and PMD structural validation
- **PMD Rules (1 Rule)**: File structure and organization validation

---

## Script Rules (20 Rules)

*These rules analyze both PMD embedded scripts and standalone .script files for comprehensive code quality validation.*

### ScriptVarUsageRule - Script Var Usage Rule

**Severity:** WARNING
**Description:** Ensures scripts use 'let' or 'const' instead of 'var' (best practice)
**Applies to:** PMD embedded scripts

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

### ScriptFileVarUsageRule - Script File Variable Usage Rule

**Severity:** WARNING
**Description:** Ensures script files follow proper variable declaration and export patterns
**Applies to:** Standalone .script files

**Why This Rule Combines Multiple Checks:**
This rule addresses two distinct quality concerns for standalone script files in a single efficient pass:
1. **Code Quality:** Modern variable declarations (`const`/`let` vs `var`)
2. **Dead Code Detection:** Unused variables and export consistency

Since both checks require parsing the same script structure and variable declarations, combining them avoids duplicate AST traversal and provides comprehensive script file validation.

**What it catches:**

- Top-level variables declared but not exported and not used internally
- Variables exported but not declared at top level
- Usage of `var` instead of `const`/`let` in script files

**Example violations:**

```javascript
// In util.script
var getCurrentTime = function() { return date:now(); };  // ❌ Should use 'const'
const unusedHelper = function() { return "unused"; };    // ❌ Not exported or used

{
  "getCurrentTime": getCurrentTime  // ❌ unusedHelper is unused
}
```

**Fix:**

```javascript
// In util.script
const getCurrentTime = function() { return date:now(); };  // ✅ Use 'const'
const helperFunction = function() { return "helper"; };    // ✅ Will be exported

{
  "getCurrentTime": getCurrentTime,
  "helperFunction": helperFunction  // ✅ Both functions exported
}
```

---

### ScriptNestingLevelRule - Script Nesting Level Rule

**Severity:** WARNING
**Description:** Ensures scripts don't have excessive nesting levels (max 4 levels)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Overly nested code structures (if statements, loops, functions)
- Code that's difficult to read and maintain due to deep nesting

**Example violations:**

```javascript
function processData(data) {
    if (data) {                    // Level 1
        if (data.isValid) {        // Level 2
            if (data.hasContent) { // Level 3
                if (data.content.length > 0) { // Level 4
                    if (data.content[0].isActive) { // Level 5 ❌ Too deep!
                        return data.content[0];
                    }
                }
            }
        }
    }
}
```

**Fix:**

```javascript
function processData(data) {
    if (!data || !data.isValid || !data.hasContent) {
        return null;
    }
  
    if (data.content.length === 0) {
        return null;
    }
  
    return data.content[0].isActive ? data.content[0] : null;
}
```

---

### ScriptComplexityRule - Script Complexity Rule

**Severity:** WARNING
**Description:** Ensures scripts don't have excessive cyclomatic complexity (max 10)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Functions with too many decision points (if/else, switch, loops, ternary operators)
- Complex functions that are hard to test and maintain
- Functions that likely need to be broken down

**Example violations:**

```javascript
function processOrder(order) {
    if (order.type === 'premium') {        // +1
        if (order.amount > 1000) {         // +1
            if (order.customer.vip) {      // +1
                // ... complex logic
            } else {                       // +1
                // ... more logic
            }
        } else if (order.amount > 500) {   // +1
            // ... logic
        }
    } else if (order.type === 'standard') { // +1
        for (let item of order.items) {    // +1
            if (item.category === 'electronics') { // +1
                // ... logic
            }
        }
    }
    // Complexity: 8+ (getting close to limit)
}
```

**Fix:**

```javascript
function processOrder(order) {
    if (order.type === 'premium') {
        return processPremiumOrder(order);
    }
  
    if (order.type === 'standard') {
        return processStandardOrder(order);
    }
  
    return processBasicOrder(order);
}

function processPremiumOrder(order) {
    // Simplified premium logic
}

function processStandardOrder(order) {
    // Simplified standard logic
}
```

---

### ScriptLongFunctionRule - Script Long Function Rule

**Severity:** WARNING
**Description:** Ensures scripts don't have excessively long functions (max 50 lines)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Functions that exceed 50 lines of code
- Monolithic functions that should be broken down
- Functions that likely violate single responsibility principle

**Example violations:**

```javascript
function processLargeDataset(data) {
    // ... 60 lines of code ...
    // This function is doing too many things
}
```

**Fix:**

```javascript
function processLargeDataset(data) {
    const validated = validateData(data);
    const processed = transformData(validated);
    return formatOutput(processed);
}

function validateData(data) {
    // ... validation logic ...
}

function transformData(data) {
    // ... transformation logic ...
}

function formatOutput(data) {
    // ... formatting logic ...
}
```

---

### ScriptFunctionParameterCountRule - Script Function Parameter Count Rule

**Severity:** WARNING
**Description:** Ensures functions don't have too many parameters (max 4)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Functions with more than 4 parameters
- Functions that are hard to call and maintain
- Functions that likely need parameter objects or refactoring

**Example violations:**

```javascript
function createUser(name, email, phone, address, age, department) { // ❌ 6 parameters
    // ... function body
}
```

**Fix:**

```javascript
function createUser(userInfo) { // ✅ Single parameter object
    const { name, email, phone, address, age, department } = userInfo;
    // ... function body
}

// Or break into smaller functions
function createUser(personalInfo, contactInfo, workInfo) { // ✅ 3 logical groups
    // ... function body
}
```

---

### ScriptConsoleLogRule - Script Console Log Rule

**Severity:** WARNING
**Description:** Ensures scripts don't contain console.log statements (production code)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- `console.log()` statements that should be removed before production
- Debug statements left in production code
- Logging that should use proper logging mechanisms

**Example violations:**

```javascript
function processData(data) {
    console.log("Processing data:", data); // ❌ Debug statement
    return data.map(item => item.value);
}
```

**Fix:**

```javascript
function processData(data) {
    // Use proper error handling instead of console.log
    if (!data || !Array.isArray(data)) {
        throw new Error("Invalid data provided");
    }
    return data.map(item => item.value);
}
```

---

### ScriptVariableNamingRule - Script Variable Naming Rule

**Severity:** INFO
**Description:** Ensures variables follow lowerCamelCase naming convention
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Variables that don't follow camelCase naming (snake_case, PascalCase, etc.)
- Inconsistent naming conventions

**Example violations:**

```javascript
const user_name = "John";     // ❌ snake_case
const UserAge = 25;           // ❌ PascalCase
const user-email = "email";   // ❌ kebab-case
```

**Fix:**

```javascript
const userName = "John";      // ✅ lowerCamelCase
const userAge = 25;           // ✅ lowerCamelCase
const userEmail = "email";    // ✅ lowerCamelCase
```

---

### ScriptFunctionalMethodUsageRule - Script Functional Method Usage Rule

**Severity:** INFO
**Description:** Recommends using functional methods (map, filter, forEach) instead of manual loops
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Traditional for loops that could be replaced with functional methods
- Code that's more verbose than necessary

**Example violations:**

```javascript
const results = [];
for (let i = 0; i < items.length; i++) {  // ❌ Manual loop
    if (items[i].active) {
        results.add(items[i].name);
    }
}
```

**Fix:**

```javascript
const results = items
    .filter(item => item.active)     // ✅ Functional approach
    .map(item => item.name);
```

---

### ScriptMagicNumberRule - Script Magic Number Rule

**Severity:** INFO
**Description:** Ensures scripts don't contain magic numbers (use named constants)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Numeric literals without clear meaning
- Hard-coded numbers that should be constants

**Example violations:**

```javascript
function calculateDiscount(price) {
    if (price > 1000) {        // ❌ Magic number
        return price * 0.15;   // ❌ Magic number
    }
    return price * 0.05;       // ❌ Magic number
}
```

**Fix:**

```javascript
const premiumThreshold = 1000;
const premiumDiscount = 0.15;
const standardDiscount = 0.05;

function calculateDiscount(price) {
    if (price > premiumThreshold) {
        return price * premiumDiscount;
    }
    return price * standardDiscount;
}
```

---

### ScriptNullSafetyRule - Script Null Safety Rule

**Severity:** WARNING
**Description:** Ensures property access chains are protected against null reference exceptions
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Unsafe property access that could throw null reference exceptions
- Missing null checks before property access
- Improper use of null coalescing operator

**Example violations:**

```javascript
const skill = workerData.skills[0].name;  // ❌ Unsafe - skills could be null/undefined
const isProgrammer = workerData.skills[0] == 'Programming' ?? false; // ❌ Won't work as expected
```

**Fix:**

```javascript
const skills = workerData.skills ?? [];      // ✅ Null coalescing fallback
const isProgrammer = skills.length > 0 && skills[0] == 'Programming'; // ✅ Safe comparison
```

---

### ScriptDescriptiveParameterRule - Script Descriptive Parameter Rule

**Severity:** INFO
**Description:** Ensures functional method parameters use descriptive names instead of single letters (except 'i', 'j', 'k' for indices)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Single-letter parameters in functional methods that make code hard to read
- Nested functional methods with confusing parameter names
- Non-descriptive variable names in map, filter, find, forEach, reduce, sort

**Example violations:**

```javascript
// ❌ Confusing single-letter parameters
const activeUsers = users.filter(x => x.active);
const userNames = users.map(u => u.name);

// ❌ Nested functional methods with same parameter name
const result = departments
    .map(x => x.teams)
    .filter(x => x.active);  // Which 'x' is which?

// ❌ Non-descriptive reduce parameters
const total = numbers.reduce((a, b) => a + b, 0);
```

**Fix:**

```javascript
// ✅ Descriptive parameter names
const activeUsers = users.filter(user => user.active);
const userNames = users.map(user => user.name);

// ✅ Clear nested functional methods
const result = departments
    .map(dept => dept.teams)
    .filter(team => team.active);

// ✅ Descriptive reduce parameters
const total = numbers.reduce((acc, num) => acc + num, 0);
```

**Special Cases:**

- **Index variables:** `i`, `j`, `k` are allowed (universally accepted)
- **Reduce methods:** Suggests `acc` for accumulator, contextual names for items
- **Sort methods:** Suggests `a`, `b` for comparison parameters
- **Context-aware:** Suggests `user` for `users.map()`, `team` for `teams.filter()`, etc.

**Configuration:**

```json
{
  "ScriptDescriptiveParameterRule": {
    "enabled": true,
    "severity_override": "WARNING",
    "custom_settings": {
      "allowed_single_letters": ["i", "j", "k"],
      "additional_functional_methods": []
    }
    }
}
```

---

### ScriptFunctionReturnConsistencyRule - Script Function Return Consistency Rule

**Severity:** WARNING
**Description:** Ensures functions have consistent return patterns
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Functions with missing return statements
- Inconsistent return patterns within functions

**Example violations:**

```javascript
function processUser(user) {
    if (user.active) {
        return user.name;
    }
    // ❌ Missing return statement
}
```

**Fix:**

```javascript
function processUser(user) {
    if (user.active) {
        return user.name;
    }
    return null; // ✅ Explicit return
}
```

---

### ScriptStringConcatRule - Script String Concat Rule

**Severity:** INFO
**Description:** Recommends using template literals instead of string concatenation
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- String concatenation using + operator
- Code that would be more readable with template literals

**Example violations:**

```javascript
const message = "Hello " + userName + ", welcome to " + appName; // ❌ String concatenation
```

**Fix:**

```javascript
const message = `Hello {{userName}}, welcome to {{appName}}`; // ✅ Template literal
```

---

### ScriptVerboseBooleanCheckRule - Script Verbose Boolean Check Rule

**Severity:** INFO
**Description:** Recommends using concise boolean expressions
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Verbose boolean comparisons that can be simplified
- Redundant boolean expressions

**Example violations:**

```javascript
if (user.active == true) { }     // ❌ Verbose
if (user.active != false) { }    // ❌ Verbose
```

**Fix:**

```javascript
if (user.active) { }              // ✅ Concise
if (!user.active) { }             // ✅ Concise negation
```

---

### ScriptEmptyFunctionRule - Script Empty Function Rule

**Severity:** INFO
**Description:** Detects empty function bodies
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Functions with empty bodies
- Placeholder functions that should be implemented or removed

**Example violations:**

```javascript
function processData(data) {
    // ❌ Empty function body
}

const handler = function() { }; // ❌ Empty function
```

---

### ScriptUnusedFunctionRule - Script Unused Function Rule

**Severity:** WARNING
**Description:** Detects functions that are declared but never called
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Functions declared but never used
- Dead code that should be removed

---

### ScriptUnusedFunctionParametersRule - Script Unused Function Parameters Rule

**Severity:** INFO
**Description:** Detects unused function parameters
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Function parameters that are declared but never used
- Parameters that could be removed to simplify the function signature

**Example violations:**

```javascript
function processUser(user, options, callback) { // ❌ options and callback unused
    return user.name;
}
```

**Fix:**

```javascript
function processUser(user) { // ✅ Only used parameters
    return user.name;
}
```

---

### ScriptUnusedVariableRule - Script Unused Variable Rule

**Severity:** INFO
**Description:** Ensures all declared variables are used (prevents dead code)
**Applies to:** PMD embedded scripts and standalone .script files

**What it catches:**

- Variables declared but never used
- Dead code that increases bundle size

**Example violations:**

```javascript
function processData() {
    const unusedVar = "never used"; // ❌ Unused variable
    const result = calculateResult();
    return result;
}
```

**Fix:**

```javascript
function processData() {
    const result = calculateResult();
    return result;
}
```

---

### ScriptUnusedScriptIncludesRule - Script Unused Script Includes Rule

**Severity:** WARNING
**Description:** Detects script files that are included but never used in PMD files
**Applies to:** PMD files with script includes

**What it catches:**

- Script files in PMD include arrays that are never called
- Dead script dependencies that increase bundle size

**Example violations:**

```javascript
// In sample.pmd
{
  "include": ["util.script", "helper.script"], // ❌ helper.script never called
  "script": "<%
    const time = util.getCurrentTime(); // Only util.script is used
  %>"
}
```

**Fix:**

```javascript
// In sample.pmd
{
  "include": ["util.script"], // ✅ Only include used scripts
  "script": "<%
    const time = util.getCurrentTime();
    const result = helper.processData(); // Or add calls to helper.script
  %>"
}
```

---

## Endpoint Rules (4 Rules)

### EndpointFailOnStatusCodesRule - Endpoint Fail On Status Codes Rule

**Severity:** WARNING
**Description:** Ensures endpoints properly handle 400 and 403 error status codes
**Applies to:** PMD endpoint definitions

**What it catches:**

- Missing error handling for common HTTP status codes
- Endpoints that don't fail on some specific error responses

**Example violations:**

```json
{
  "endPoints": [{
    "name": "GetUser",
    "url": "/users/me"
    // ❌ Missing failOnStatusCodes
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "GetUser", 
    "url": "/users/me",
    "failOnStatusCodes": [
      {"code": "400"},
      {"code": "403"}
    ]
  }]
}
```

---

### EndpointNameLowerCamelCaseRule - Endpoint Name Lower Camel Case Rule

**Severity:** INFO
**Description:** Ensures endpoint names follow lowerCamelCase convention
**Applies to:** PMD endpoint definitions

**What it catches:**

- Endpoint names that don't follow camelCase naming
- Inconsistent naming conventions across endpoints

**Example violations:**

```json
{
  "endPoints": [{
    "name": "get_user_data"  // ❌ snake_case
  }, {
    "name": "GetUserProfile" // ❌ PascalCase
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "getUserData"    // ✅ lowerCamelCase
  }, {
    "name": "getUserProfile" // ✅ lowerCamelCase
  }]
}
```

---

### EndpointOnSendSelfDataRule - Endpoint On Send Self Data Rule

**Severity:** WARNING
**Description:** Ensures outbound endpoints don't use the anti-pattern 'self.data = {:}' in onSend scripts
**Applies to:** PMD outbound endpoint definitions only

**What it catches:**

- Usage of the anti-pattern `self.data = {:}` in outbound endpoint onSend scripts
- Outbound endpoints that use outdated or problematic data initialization patterns

**Example violations:**

```json
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      self.data = {:}; // ❌ Anti-pattern that should be avoided in outbound endpoints
      return self.data;
    %>"
  }]
}
```

**Fix:**

```json
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      let postData = {'name': workerName.value}; // ✅ Use a more descriptive local variable
      return postData;
    %>"
  }]
}
```

---

### EndpointBaseUrlTypeRule - Endpoint Base URL Type Rule

**Severity:** WARNING
**Description:** Ensures endpoint URLs don't include hardcoded *.workday.com or apiGatewayEndpoint values
**Applies to:** PMD endpoint definitions

**What it catches:**

- Hardcoded *.workday.com domains in endpoint URLs
- Hardcoded apiGatewayEndpoint values in URLs
- Endpoints that should use baseUrlType instead of hardcoded values

**Example violations:**

```json
{
  "endPoints": [{
    "name": "getWorker",
    "url": "https://api.workday.com/common/v1/workers/me"  // ❌ Hardcoded workday.com
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "getWorker",
    "url": "/workers/me",  // ✅ Relative URL
    "baseUrlType": "workday-common"  // ✅ Use baseUrlType instead
  }]
}
```

---

## Structure Rules (4 Rules)

### WidgetIdRequiredRule - Widget ID Required Rule

**Severity:** ERROR
**Description:** Ensures all widgets have required 'id' field
**Applies to:** PMD widget definitions

**What it catches:**

- Widgets missing required id field
- Widgets that can't be properly referenced

**Example violations:**

```json
{
  "presentation": {
    "body": {
      "type": "section",
      "children": [{
        "type": "text",
        "label": "Welcome"
        // ❌ Missing required id field
      }]
    }
  }
}
```

**Fix:**

```json
{
  "presentation": {
    "body": {
      "type": "section", 
      "children": [{
        "type": "text",
        "label": "Welcome",
        "id": "welcomeText" // ✅ Required id field
      }]
    }
  }
}
```

---

### WidgetIdLowerCamelCaseRule - Widget ID Lower Camel Case Rule

**Severity:** INFO
**Description:** Ensures widget IDs follow lowerCamelCase convention
**Applies to:** PMD widget definitions

**What it catches:**

- Widget IDs that don't follow camelCase naming
- Inconsistent naming conventions

**Example violations:**

```json
{
  "presentation": {
    "body": {
      "type": "section",
      "children": [{
        "type": "text",
        "id": "welcome_text"  // ❌ snake_case
      }, {
        "type": "button",
        "id": "UserProfile"   // ❌ PascalCase
      }]
    }
  }
}
```

**Fix:**

```json
{
  "presentation": {
    "body": {
      "type": "section",
      "children": [{
        "type": "text",
        "id": "welcomeText"   // ✅ lowerCamelCase
      }, {
        "type": "button", 
        "id": "userProfile"   // ✅ lowerCamelCase
      }]
    }
  }
}
```

---

### FooterPodRequiredRule - Footer Pod Required Rule

**Severity:** INFO
**Description:** Ensures footer widgets utilize pods
**Applies to:** PMD footer widget definitions

**What it catches:**

- Footer widgets that should use pod components
- Missing pod references in footer widgets

---

### StringBooleanRule - String Boolean Rule

**Severity:** INFO
**Description:** Ensures boolean values are not stored as strings
**Applies to:** PMD configuration values

**What it catches:**

- Boolean values stored as strings ("true"/"false")
- Configuration that should use proper boolean types

**Example violations:**

```json
{
  "type": "text",
  "id": "welcomeMessage",
  "visible": "true",  // ❌ String instead of boolean
  "enabled": "false"  // ❌ String instead of boolean
}
```

**Fix:**

```json
{
  "type": "text",
  "id": "welcomeMessage",
  "visible": true,    // ✅ Proper boolean
  "enabled": false    // ✅ Proper boolean
}
```

---

## PMD Rules (1 Rule)

### PMDSectionOrderingRule - PMD Section Ordering Rule

**Severity:** INFO (configurable)
**Description:** Ensures PMD file root-level sections follow consistent ordering for better readability
**Applies to:** PMD file structure
**Configurable:** ✅ Section order and enforcement can be customized

**What it catches:**

- PMD sections in non-standard order
- Inconsistent file structure across applications

**Default Section Order:**

1. `id`
2. `securityDomains`
3. `include`
4. `script`
5. `endPoints`
6. `onSubmit`
7. `outboundData`
8. `onLoad`
9. `presentation`

**Example violations:**

```json
{
  "presentation": { },     // ❌ presentation should come last
  "id": "myApp",
  "script": "<%  %>",
  "include": ["util.script"]
}
```

**Fix:**

```json
{
  "id": "myApp",           // ✅ Proper order
  "include": ["util.script"],
  "script": "<%  %>",
  "presentation": { }
}
```

**Configuration:**

```json
{
  "PMDSectionOrderingRule": {
    "enabled": true,
    "custom_settings": {
        "section_order": ["id", "securityDomains", "include", "script", "endPoints", "onSubmit", "outboundData", "onLoad", "presentation"]
    }
  }
}
```

---

## Rule Configuration

All rules can be configured in your configuration files:

- **`configs/default.json`** - Standard configuration
- **`configs/minimal.json`** - Minimal rule set
- **`configs/comprehensive.json`** - All rules enabled with strict settings

### Configuration Options

Each rule supports:

- **`enabled`** - Enable/disable the rule
- **`severity_override`** - Override default severity (SEVERE, WARNING, INFO)
- **`custom_settings`** - Rule-specific configuration options

### Example Configuration

```json
{
  "ScriptComplexityRule": {
    "enabled": true,
    "severity_override": "SEVERE",
    "custom_settings": {
      "max_complexity": 8
    }
  },
  "PMDSectionOrderingRule": {
    "enabled": true,
    "custom_settings": {
      "section_order": ["id", "presentation", "script"]
    }
  }
}
```

---

## Summary

The Arcane Auditor channels mystical powers through **29 rules** across **4 categories**:

- ✅ **20 Script Rules** - Code quality for PMD and standalone scripts
- ✅ **4 Endpoint Rules** - API validation and compliance
- ✅ **4 Structure Rules** - Widget and component validation
- ✅ **1 PMD Rule** - File organization and structure

These rules help maintain consistent, high-quality Workday Extend applications by catching issues that compilers aren't designed to catch, but are important for maintainability, performance, and team collaboration.
