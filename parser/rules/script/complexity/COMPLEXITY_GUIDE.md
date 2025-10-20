# Script Complexity Rule Guide

## Overview

The Script Complexity Rule (ScriptComplexityRule) measures cyclomatic complexity to identify functions that are too complex and should be refactored. Complexity is calculated by counting decision points in the code.

## Complexity Calculation

**Base Complexity**: Every function starts with a complexity of 1.

**Constructs that add +1 complexity**:

### Control Flow Statements
- **if statements** (`if`) - Each if creates a decision point
- **while loops** (`while`) - Loop condition creates a decision point  
- **for loops** (`for`) - Loop condition creates a decision point
- **do-while loops** (`do`) - Loop condition creates a decision point

### Logical Operators
- **Logical AND** (`&&`) - Each && operator creates a decision point
- **Logical OR** (`||`) - Each || operator creates a decision point

### Conditional Expressions
- **Ternary operator** (`?:`) - Conditional expression creates a decision point

## Examples

### Simple Function (Complexity: 1)
```javascript
const simpleFunction = function() {
    return "hello";
};
```

### Function with if statement (Complexity: 2)
```javascript
const checkValue = function(value) {
    if (value > 0) {
        return "positive";
    }
    return "zero or negative";
};
```

### Function with multiple conditions (Complexity: 4)
```javascript
const complexFunction = function(a, b) {
    if (a > 0) {           // +1
        if (b < 0) {       // +1
            return "a positive, b negative";
        }
    }
    return a && b;         // +1 (logical AND)
};
```

### Function with loops and conditions (Complexity: 6)
```javascript
const processItems = function(items) {
    for (let i = 0; i < items.length; i++) {  // +1 (for loop)
        if (items[i] > 0) {                   // +1 (if statement)
            if (items[i] < 100) {             // +1 (nested if)
                console.log(items[i]);
            }
        }
    }
    return items.length > 0 ? "processed" : "empty";  // +1 (ternary)
};
```

## Recommended Limits

- **Maximum complexity**: 10
- **Functions exceeding this limit** should be refactored into smaller, more focused functions

## Refactoring Strategies

1. **Extract methods**: Move complex logic into separate functions
2. **Simplify conditions**: Use early returns to reduce nesting
3. **Break down loops**: Split complex loops into multiple simpler ones
4. **Use lookup tables**: Replace complex if-else chains with maps or arrays

## What is NOT counted

- **Function declarations**: Function bodies don't add complexity to the parent
- **Variable assignments**: Simple assignments don't create decision points
- **Function calls**: Calling other functions doesn't add complexity
- **Arithmetic operations**: Basic math operations don't create decision points
- **String operations**: String manipulation doesn't add complexity

## Notes

- **Nested functions**: Each function is analyzed independently
- **Inline functions**: Functions nested more than 1 level deep are ignored
- **Procedural code**: Code outside functions is also analyzed for complexity
