"""Script cyclomatic complexity rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .cyclomatic_complexity_detector import CyclomaticComplexityDetector


class ScriptComplexityRule(ScriptRuleBase):
    """Rule to check for excessive cyclomatic complexity."""

    DESCRIPTION = "Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)"
    SEVERITY = "ADVICE"
    DETECTOR = CyclomaticComplexityDetector
    AVAILABLE_SETTINGS = {
        'max_complexity': {
            'type': 'number',
            'default': 10,
            'description': 'Maximum allowed cyclomatic complexity per function. Functions exceeding this threshold will be flagged.',
            'minimum': 1,
            'maximum': 50
        }
    }
    
    DOCUMENTATION = {
        'why': '''Cyclomatic complexity measures the number of independent paths through your code (every *if*, *else*, *loop*, etc. adds to it). High complexity (default threshold: 10, configurable) means your function has too many decision points, making it exponentially harder to test all scenarios and increasing the chance of bugs. Breaking complex functions into smaller, focused ones makes testing easier and reduces defects.

**🧙‍♂️ Wizard's Note:** This rule currently evaluates **either** individual functions **or** procedural script blocks, but not both mixed together. If your script has inline function declarations, only those functions are checked; the procedural code between functions is not separately analyzed for complexity.''',
        'catches': [
            'Functions with too many decision points (*if*/*else*, *loops*, *ternary operators*, etc.)',
            'Complex functions that are hard to test and maintain',
            'Functions that likely need to be broken down',
            'Each top-level function is analyzed separately',
            'For pure procedural scripts (no functions), the entire script block is analyzed'
        ],
        'examples': '''**Example violations:**

```javascript
const processOrder = function(order) {
    // Function starts with score of 1 as base

    const highValueMin = 1000;
    const discountMin = 500;
    const vipYearMin = 5

    // Decision point +1: if
    if (order.type == 'premium') {
        // Decision point +1: if
        if (order.amount > highValueMin) {
            // Decision point +1: if
            if (order.customer.vip) {
                // Decision point +1: if
                if (order.customer.loyaltyYears > vipYearMin) {
                    applyVIPDiscount();
                }
            }
            // Decision point +1: if
            if (order.shippingAddress.country == 'US') {
                applyDomesticShipping();
            }
        // Decision point +1: else if
        } else if (order.amount > discountMin) {
            applyStandardDiscount();
        }
    // Decision point +1: else if
    } else if (order.type == 'standard') {
        // Decision point +1: for
        for (var i = 0; i < order.items.length; i++) {
            // Decision point +1: if
            if (order.items[i].category == 'electronics') {
                // Decision point +1: if
                if (order.items[i].warrantyRequired) {
                    addWarranty(order.items[i]);
                }
            // Decision point +1: else if (EXCEEDS THRESHOLD)
            } else if (order.items[i].category == 'clothing') {
                applyClothingTax();
            }
        }
    }
    // Cyclomatic Complexity: 12 (exceeds default threshold of 10)
}
```

**Fix:**

Break the function into smaller, focused functions:

```javascript
const processOrder = function(order) {
    if (order.type == 'premium') {
        processPremiumOrder(order);
    } else if (order.type == 'standard') {
        processStandardOrder(order);
    }
    // Complexity: 3 ✅
}

const processPremiumOrder = function(order) {
    const highValueMin = 1000;
    const discountMin = 500;

    if (order.amount > maxAmount) {
        processHighValueOrder(order);
    } else if (order.amount > discountMin) {
        applyStandardDiscount();
    }
    // Complexity: 3 ✅
}

const processHighValueOrder = function(order) {
    if (order.customer.vip && order.customer.loyaltyYears > 5) {
        applyVIPDiscount();
    }
    if (order.shippingAddress.country == 'US') {
        applyDomesticShipping();
    }
    // Complexity: 4 ✅
}

const processStandardOrder = function(order) {
    order.items.forEach(item => {
      processOrderItem(item);
    })
    // Complexity: 1 ✅
}

const processOrderItem = function(item) {
    if (item.category == 'electronics' && item.warrantyRequired) {
        addWarranty(item);
    } else if (item.category == 'clothing') {
        applyClothingTax();
    }
    // Complexity: 4 ✅
}
```''',
        'recommendation': 'Break complex functions into smaller, focused functions with fewer decision points. Each function should handle a single responsibility, making the code easier to test and maintain. Aim for cyclomatic complexity below the configured threshold (default: 10). You can adjust the threshold in your rule configuration if your team has different complexity standards.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
