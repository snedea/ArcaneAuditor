import inspect
import pkgutil
from typing import List, Optional

# --- Local Imports ---
from .models import ProjectContext
from . import rules
from .rules.base import Rule, Finding
from .config import ExtendReviewerConfig

class RulesEngine:
    """Discovers, loads, and runs all analysis rules."""

    def __init__(self, config: Optional[ExtendReviewerConfig] = None):
        self.config = config or ExtendReviewerConfig()
        self.rules = self._discover_rules()

    def _discover_rules(self) -> List[Rule]:
        """
        Automatically finds and instantiates all Rule classes in the 'rules' package.
        Only includes rules that are enabled in the configuration.
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
                    
                    # Check if rule is enabled in configuration
                    if self.config.is_rule_enabled(member_obj.ID):
                        print(f"🔎 Discovered rule: {member_obj.ID}")
                        rule_instance = member_obj()
                        # Apply configuration overrides
                        self._apply_rule_config(rule_instance)
                        discovered_rules.append(rule_instance)
                    else:
                        print(f"⏭️  Skipping disabled rule: {member_obj.ID}")
        return discovered_rules
    
    def _apply_rule_config(self, rule: Rule) -> None:
        """Apply configuration overrides to a rule instance."""
        # Override severity if configured
        if hasattr(rule, 'SEVERITY'):
            original_severity = rule.SEVERITY
            configured_severity = self.config.get_rule_severity(rule.ID, original_severity)
            if configured_severity != original_severity:
                rule.SEVERITY = configured_severity
                print(f"🔧 Override severity for {rule.ID}: {original_severity} → {configured_severity}")
        
        # Apply custom settings if the rule supports it
        custom_settings = self.config.get_rule_settings(rule.ID)
        if custom_settings and hasattr(rule, 'apply_settings'):
            rule.apply_settings(custom_settings)

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