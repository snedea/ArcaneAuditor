// ArcaneAuditor Rules Data
// Generated from RULE_BREAKDOWN.md

const RULES_DATA = {
  scriptRules: [
    {
      id: 1,
      name: "ScriptVarUsageRule",
      severity: "ADVICE",
      category: "Script",
      description: "Ensures scripts use 'let' or 'const' instead of 'var' (best practice)",
      appliesTo: "PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files",
      configurable: false,
      whyMatters: "The `var` keyword has function scope, which can cause unexpected behavior and bugs when the same name is reused in nested blocks. Using `let` (block scope) and `const` (immutable) makes your code more predictable and prevents accidental variable shadowing issues. Using the `const` keyword is also a good way to communicate `intent` to your readers.",
      catches: [
        "Usage of `var` declarations instead of modern `let`/`const`",
        "Variable declarations that don't follow Extend best practices"
      ],
      violationExample: `var myVariable = "value";  // ❌ Should use 'let' or 'const'`,
      fixExample: `const myVariable = "value";  // ✅ Use 'const' for immutable values
let myVariable = "value";    // ✅ Use 'let' for mutable values`
    },
    {
      id: 2,
      name: "ScriptDeadCodeRule",
      severity: "ADVICE",
      category: "Script",
      description: "Validates export patterns in standalone script files by detecting declared variables that are never exported or used",
      appliesTo: "Standalone .script files and their export patterns",
      configurable: false,
      whyMatters: "Dead code in standalone script files increases your application's bundle size and memory footprint, making pages load slower. Every unused function or constant is still parsed and loaded, wasting resources. This is especially important in Workday Extend where script files are shared across pages - dead code multiplies the performance impact.",
      catches: [
        "Top-level variables (of any type) declared but not exported AND not used internally",
        "Function-scoped variables that are declared but never used",
        "Dead code that increases bundle size unnecessarily"
      ],
      violationExample: `// In util.script
const getCurrentTime = function() { return date:now(); };
const unusedHelper = function() { return "unused"; };    // ❌ Dead code
const apiUrl = "https://api.example.com";  // ❌ Dead code

{
  "getCurrentTime": getCurrentTime
}`,
      fixExample: `// In util.script
const getCurrentTime = function() { return date:now(); };
const helperFunction = function() { return "helper"; };
const apiUrl = "https://api.example.com";

{
  "getCurrentTime": getCurrentTime,
  "helperFunction": helperFunction,
  "apiUrl": apiUrl  // ✅ All declarations are exported
}`
    },
    {
      id: 3,
      name: "ScriptNestingLevelRule",
      severity: "ADVICE",
      category: "Script",
      description: "Ensures scripts don't have excessive nesting levels (default max 4 levels)",
      appliesTo: "All script code including PMD scripts, Pod endpoint/widget scripts, and standalone .script files",
      configurable: true,
      whyMatters: "Deep nesting (more than 4 levels of if/for/while statements) makes code exponentially harder to read, test, and debug. Each nesting level adds cognitive load and makes it difficult to understand the logic flow. Research shows that code with deep nesting has significantly higher bug rates and takes longer to maintain.",
      catches: [
        "Overly nested code structures (if statements, loops, functions)",
        "Code that's difficult to read and maintain due to deep nesting"
      ],
      configurationExample: `{
  "ScriptNestingLevelRule": {
    "enabled": true,
    "custom_settings": {
      "max_nesting_level": 5  // Increase from default 4 if needed
    }
  }
}`,
      violationExample: `function processData(data) {
    if (!empty data) { // Level 1
        if (data.isValid) { // Level 2
            if (data.hasContent) { // Level 3
                if (data.content.size() > 0) { // Level 4
                    if (data.content[0].isActive) { // Level 5 ❌ Too deep!
                        return data.content[0];
                    }
                }
            }
        }
    }
}`,
      fixExample: `function processData(data) {
    if (empty data.content || !data.isValid || !data.hasContent) {
        return null;
    }
    return data.content[0].isActive ? data.content[0] : null;
}`
    },
    {
      id: 4,
      name: "ScriptComplexityRule",
      severity: "ADVICE",
      category: "Script",
      description: "Ensures scripts don't have excessive cyclomatic complexity (max 10)",
      appliesTo: "All script functions in PMD scripts, Pod scripts, and .script files",
      configurable: true,
      whyMatters: "Cyclomatic complexity measures the number of independent paths through your code. High complexity (>10) makes testing exponentially harder and increases the chance of bugs. Functions with high complexity are difficult to understand, test thoroughly, and maintain over time. Breaking complex functions into smaller, focused functions improves code quality and reduces defects.",
      catches: [
        "Functions with too many decision points (if/else, loops, ternary operators, etc.)",
        "Complex functions that are hard to test and maintain",
        "Functions that should be refactored into smaller, focused functions"
      ],
      configurationExample: `{
  "ScriptComplexityRule": {
    "enabled": true,
    "custom_settings": {
      "max_complexity": 12  // Increase from default 10 if needed
    }
  }
}`,
      violationExample: `const processOrder = function(order) {
    if (order.type == 'premium') {
        if (order.amount > 1000) {
            if (order.customer.vip) {
                if (order.customer.loyaltyYears > 5) {
                    applyVIPDiscount();
                }
            }
            if (order.shippingAddress.country == 'US') {
                applyDomesticShipping();
            }
        } else if (order.amount > 500) {
            applyStandardDiscount();
        }
    } else if (order.type == 'standard') {
        for (var i = 0; i < order.items.length; i++) {
            if (order.items[i].category == 'electronics') {
                if (order.items[i].warrantyRequired) {
                    addWarranty(order.items[i]);
                }
            } else if (order.items[i].category == 'clothing') {
                applyClothingTax();
            }
        }
    }
    // Complexity: 12 ❌
}`,
      fixExample: `const processOrder = function(order) {
    if (order.type == 'premium') {
        processPremiumOrder(order);
    } else if (order.type == 'standard') {
        processStandardOrder(order);
    }
    // Complexity: 3 ✅
}`
    },
    {
      id: 5,
      name: "ScriptConsoleLogRule",
      severity: "ACTION",
      category: "Script",
      description: "Ensures scripts don't contain console log statements (for production code)",
      appliesTo: "All script code in PMD, Pod, and .script files",
      configurable: false,
      whyMatters: "Console statements left in production code can expose sensitive data in production logs, create performance overhead, and clutter browser consoles for end users. They're debugging artifacts that should be removed before deployment. In Workday Extend, console statements can expose sensitive business data like employee information, salary details, or organizational structures in browser logs.",
      catches: [
        "console log statements that should be removed before production",
        "Debug statements left in production code"
      ],
      violationExample: `function processData(data) {
    console.debug("Processing data:", data); // ❌ Debug statement
    return data.map(item => item.value);
}`,
      fixExample: `function processData(data) {
    // Comment out or remove
    // console.debug("Processing data:", data);
    return data.map(item => item.value);
}`
    },
    {
      id: 6,
      name: "ScriptArrayMethodUsageRule",
      severity: "ADVICE",
      category: "Script",
      description: "Recommends using array higher-order methods (map, filter, forEach) instead of manual loops",
      whyMatters: "Array methods like map, filter, and forEach are more concise, less error-prone (no off-by-one errors), and communicate intent better than manual for-loops.",
      catches: [
        "Traditional for loops that could be replaced with array higher-order methods",
        "Code that's more verbose than necessary"
      ],
      violationExample: `const results = [];
for (let i = 0; i < items.length; i++) {  // ❌ Manual loop
    if (items[i].active) {
        results.add(items[i].name);
    }
}`,
      fixExample: `const results = items
    .filter(item => item.active)     // ✅ Array higher-order methods
    .map(item => item.name);`
    },
    {
      id: 7,
      name: "ScriptMagicNumberRule",
      severity: "ADVICE",
      category: "Script",
      description: "Ensures scripts don't contain magic numbers (use named constants)",
      whyMatters: "Magic numbers hide meaning and make code harder to maintain. Named constants make the purpose clear and provide a single source of truth.",
      catches: [
        "Numeric literals without clear meaning",
        "Hard-coded numbers that should be constants"
      ],
      violationExample: `function calculateDiscount(price) {
    if (price > 1000) {        // ❌ Magic number
        return price * 0.15;   // ❌ Magic number
    }
    return price * 0.05;       // ❌ Magic number
}`,
      fixExample: `const premiumThreshold = 1000;
const premiumDiscount = 0.15;
const standardDiscount = 0.05;

function calculateDiscount(price) {
    if (price > premiumThreshold) {
        return price * premiumDiscount;
    }
    return price * standardDiscount;
}`
    },
    {
      id: 8,
      name: "ScriptVariableNamingRule",
      severity: "ADVICE",
      category: "Script",
      description: "Ensures variables follow lowerCamelCase naming convention",
      whyMatters: "Consistent naming conventions make code easier to read and reduce cognitive load. lowerCamelCase is the standard for variables.",
      catches: [
        "Variables that don't follow lowerCamelCase naming (snake_case, PascalCase, etc.)",
        "Inconsistent naming conventions"
      ],
      violationExample: `const user_name = "John";     // ❌ snake_case
const UserAge = 25;           // ❌ PascalCase`,
      fixExample: `const userName = "John";      // ✅ lowerCamelCase
const userAge = 25;           // ✅ lowerCamelCase`
    }
  ],
  structureRules: [
    {
      id: 24,
      name: "HardcodedWorkdayAPIRule",
      severity: "ACTION",
      category: "Structure",
      description: "Detects hardcoded *.workday.com URLs that should use apiGatewayEndpoint",
      appliesTo: "AMD dataProviders and PMD/POD endpoint definitions",
      configurable: false,
      whyMatters: "Hardcoded workday.com URLs are not update safe and lack regional awareness. Using apiGatewayEndpoint ensures your endpoints work across all environments and tenant types (production, sandbox, implementation). Hard-coded URLs will break when deploying to different regions or when Workday updates their API infrastructure.",
      catches: [
        "Hardcoded *.workday.com URLs in AMD dataProviders",
        "Hardcoded *.workday.com URLs in PMD/POD endpoints",
        "Non-portable endpoint configurations that won't work across environments"
      ],
      violationExample: `{
  "name": "getWorker",
  "url": "https://api.workday.com/common/v1/workers/me"  // ❌ Hardcoded
}`,
      fixExample: `{
  "name": "getWorker",
  "url": "<% apiGatewayEndpoint + '/common/v1/workers/me' %>"  // ✅ Dynamic
}`
    },
    {
      id: 25,
      name: "EndpointFailOnStatusCodesRule",
      severity: "ACTION",
      category: "Structure",
      description: "Ensures endpoints properly handle 400 and 403 error status codes",
      appliesTo: "AMD, PMD, and POD endpoint configurations",
      configurable: false,
      whyMatters: "Without proper error handling, endpoints silently swallow errors causing data inconsistencies and debugging nightmares. When an API returns a 400 (Bad Request) or 403 (Forbidden) status, your application needs to know about it to handle the error gracefully. Without failOnStatusCodes, these errors are silently ignored, leading to incomplete data loads, confusing user experiences, and hours of debugging to find why data isn't appearing correctly.",
      catches: [
        "Missing error handling for 4xx status codes",
        "Endpoints without failOnStatusCodes configuration",
        "Silent error scenarios that cause data inconsistencies"
      ],
      violationExample: `{
  "endPoints": [{
    "name": "getCurrentUser",
    "url": "/users/me"
    // ❌ Missing failOnStatusCodes
  }]
}`,
      fixExample: `{
  "endPoints": [{
    "name": "getCurrentUser",
    "url": "/users/me",
    "failOnStatusCodes": [
      {"code": 400},
      {"code": 403}
    ]  // ✅ Proper error handling
  }]
}`
    },
    {
      id: 26,
      name: "WidgetIdRequiredRule",
      severity: "ACTION",
      category: "Structure",
      description: "Ensures all widgets have an 'id' field set",
      appliesTo: "PMD and POD widget structures",
      configurable: true,
      whyMatters: "Widget IDs are essential for referencing widgets in scripts (to get/set values, show/hide, etc.) and for debugging. Without IDs, you can't interact with widgets programmatically, making dynamic behavior impossible. IDs also help identify widgets in error messages and make code maintenance much easier when you need to find where a widget is defined or used. There are also known issues where missing IDs will result in logs not showing the data someone may expect (i.e. a panelList widget may not log its values without all IDs set).",
      catches: [
        "Widgets missing required 'id' field"
      ],
      smartExclusions: "Built-in widget types that don't require IDs: footer, item, group, title, pod, cardContainer, card, instanceList, taskReference, editTasks, multiSelectCalendar, bpExtender, hub, and column objects (which use columnId instead).",
      configurationExample: `{
  "WidgetIdRequiredRule": {
    "enabled": true,
    "custom_settings": {
      "excluded_widget_types": ["section", "fieldSet"]
    }
  }
}`,
      violationExample: `{
  "type": "richText",  // ❌ Missing id field
  "label": "Welcome",
  "value": "Hello, user!"
}`,
      fixExample: `{
  "type": "richText",
  "id": "welcomeMessage",  // ✅ Added id field
  "label": "Welcome",
  "value": "Hello, user!"
}`
    },
    {
      id: 27,
      name: "PMDSecurityDomainRule",
      severity: "ACTION",
      category: "Structure",
      description: "Ensures PMD pages have at least one security domain defined (excludes microConclusion and error pages unless strict mode is enabled)",
      appliesTo: "PMD file security configuration",
      configurable: true,
      whyMatters: "Security domains control who can access your PMD pages in Workday. Missing security domains means your page is accessible to all users, which could lead to a security incident.",
      catches: [
        "PMD pages missing securityDomains list",
        "Empty securityDomains arrays",
        "Enforces security best practices for Workday applications"
      ],
      smartExclusions: "MicroConclusion pages (pages with presentation.microConclusion: true) are excluded unless strict mode is enabled. Error pages (pages whose ID appears in SMD errorPageConfigurations) are excluded unless strict mode is enabled. Only enforces security domains on pages that actually need them (unless strict mode).",
      configurationExample: `{
  "PMDSecurityDomainRule": {
    "enabled": true,
    "custom_settings": {
      "strict": true  // Require security domains for ALL pages
    }
  }
}`,
      violationExample: `{
  "id": "myPage",
  "presentation": {
    "body": { }
  }
  // ❌ Missing security domains
}`,
      fixExample: `{
  "id": "myPage",
  "securityDomains": ["ViewAdminPages"],  // ✅ Security defined
  "presentation": {
    "body": { }
  }
}`
    },
    {
      id: 28,
      name: "FileNameLowerCamelCaseRule",
      severity: "ADVICE",
      category: "Structure",
      description: "Ensures all file names follow lowerCamelCase naming convention",
      appliesTo: "All Extend files (.pmd, .pod, .amd, .smd, .script, etc.)",
      configurable: false,
      whyMatters: "LowerCamelCase is the Workday Extend standard, ensuring files are organized predictably and consistently across all projects. Consistent naming makes it easier for teams to find files, reduces cognitive load when reading code, and prevents naming conflicts. Following this convention also makes your code more maintainable and aligns with Workday's development best practices.",
      catches: [
        "Files using PascalCase, snake_case, or UPPERCASE",
        "Files starting with numbers",
        "Inconsistent file naming that violates Workday Extend standards"
      ],
      violationExample: `MyPage.pmd              // ❌ PascalCase
worker_detail.pmd       // ❌ snake_case`,
      fixExample: `myPage.pmd              // ✅ lowerCamelCase
workerDetail.pmd        // ✅ lowerCamelCase`
    }
  ]
};

// Export for use in game
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RULES_DATA;
}
