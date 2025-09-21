import inspect
import pkgutil
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Local Imports ---
from .models import ProjectContext
from . import rules
from .rules.base import Rule, Finding
from .config import ArcaneAuditorConfig

class RulesEngine:
    """Discovers, loads, and runs all analysis rules."""

    def __init__(self, config: Optional[ArcaneAuditorConfig] = None):
        self.config = config or ArcaneAuditorConfig()
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
                    
                    # Skip example rules (flagged with IS_EXAMPLE = True)
                    if hasattr(member_obj, 'IS_EXAMPLE') and member_obj.IS_EXAMPLE:
                        continue
                    
                    # Check if rule is enabled in configuration using class name
                    if self.config.is_rule_enabled(member_obj.__name__):
                        print(f"Discovered rule: {member_obj.__name__}")
                        rule_instance = member_obj()
                        # Apply configuration overrides
                        self._apply_rule_config(rule_instance)
                        discovered_rules.append(rule_instance)
                    else:
                        print(f"Skipping disabled rule: {member_obj.__name__}")
        return discovered_rules
    
    def _apply_rule_config(self, rule: Rule) -> None:
        """Apply configuration overrides to a rule instance."""
        # Override severity if configured
        if hasattr(rule, 'SEVERITY'):
            original_severity = rule.SEVERITY
            configured_severity = self.config.get_rule_severity(rule.__class__.__name__, original_severity)
            if configured_severity != original_severity:
                rule.SEVERITY = configured_severity
                print(f"🔧 Override severity for {rule.__class__.__name__}: {original_severity} → {configured_severity}")
        
        # Apply custom settings if the rule supports it
        custom_settings = self.config.get_rule_settings(rule.__class__.__name__)
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
            print("No rules were found to run.")
            return []
            
        print(f"\nRunning {len(self.rules)} rule(s)...")
        
        # For small rule counts, use serial processing to avoid overhead
        if len(self.rules) <= 5:
            print("Using serial rule execution (small rule count)")
            for rule in self.rules:
                try:
                    # The 'analyze' method is a generator, so we consume it into a list.
                    findings_from_rule = list(rule.analyze(context))
                    if findings_from_rule:
                        all_findings.extend(findings_from_rule)
                except Exception as e:
                    print(f"Rule {rule.__class__.__name__} failed: {e}")
        else:
            # Use parallel processing for larger rule sets
            max_workers = min(8, len(self.rules))  # Cap at 8 workers for rules
            print(f"Using parallel rule execution ({max_workers} workers for {len(self.rules)} rules)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all rule execution tasks
                future_to_rule = {
                    executor.submit(self._run_rule_safe, rule, context): rule
                    for rule in self.rules
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_rule):
                    rule = future_to_rule[future]
                    try:
                        findings_from_rule = future.result()
                        if findings_from_rule:
                            all_findings.extend(findings_from_rule)
                    except Exception as e:
                        print(f"Error running rule {rule.__class__.__name__}: {e}")
        
        print(f"Analysis complete. Found {len(all_findings)} issue(s).")
        return all_findings
    
    def _run_rule_safe(self, rule: Rule, context: ProjectContext) -> List[Finding]:
        """Thread-safe wrapper for running a single rule."""
        try:
            return list(rule.analyze(context))
        except Exception as e:
            print(f"Rule {rule.__class__.__name__} failed: {e}")
            return []