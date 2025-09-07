import inspect
import pkgutil
from typing import List

# --- Local Imports ---
from .models import ProjectContext
from . import rules
from .rules.base import Rule, Finding

class RulesEngine:
    """Discovers, loads, and runs all analysis rules."""

    def __init__(self):
        self.rules = self._discover_rules()

    def _discover_rules(self) -> List[Rule]:
        """
        Automatically finds and instantiates all Rule classes in the 'rules' package.
        """
        discovered_rules = []
        # pkgutil.walk_packages allows us to find all modules in a package
        for _, name, _ in pkgutil.walk_packages(rules.__path__, f"{rules.__name__}."):
            # Import the module
            module = __import__(name, fromlist="dummy")
            # Find all classes in the module that are subclasses of Rule
            for member_name, member_obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(member_obj, Rule) and member_obj is not Rule:
                    # Skip abstract classes
                    if hasattr(member_obj, '__abstractmethods__') and member_obj.__abstractmethods__:
                        continue
                    # Skip the base Rule class itself
                    if member_obj.__name__ == 'Rule':
                        continue
                    print(f"🔎 Discovered rule: {member_obj.ID}")
                    discovered_rules.append(member_obj()) # Instantiate the rule
        return discovered_rules

    def run(self, context: ProjectContext) -> List[Finding]:
        """

        Executes all discovered rules against the project context.

        Args:
            context: The ProjectContext containing the entire application model.

        Returns:
            A list of all findings from all rules.
        """
        all_findings = []
        if not self.rules:
            print("⚠️ No rules were found to run.")
            return []
            
        print(f"\n⚙️  Running {len(self.rules)} rule(s)...")
        for rule in self.rules:
            try:
                # The 'analyze' method is a generator, so we consume it into a list.
                findings_from_rule = list(rule.analyze(context))
                if findings_from_rule:
                    all_findings.extend(findings_from_rule)
            except Exception as e:
                print(f"❌ Error running rule {rule.ID}: {e}")
        
        print(f"✅ Analysis complete. Found {len(all_findings)} issue(s).")
        return all_findings