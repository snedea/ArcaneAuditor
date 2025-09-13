import React, { useState, useEffect } from 'react';
import { Settings, Save, Loader } from 'lucide-react';
import { Rule, Configuration } from '../types/analysis';

const ConfigurationPanel: React.FC = () => {
  const [rules, setRules] = useState<Rule[]>([]);
  const [configurations, setConfigurations] = useState<Configuration[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadRules();
    loadConfigurations();
  }, []);

  const loadRules = async () => {
    try {
      const response = await fetch('/api/rules');
      if (response.ok) {
        const data = await response.json();
        setRules(data.rules);
      }
    } catch (error) {
      console.error('Failed to load rules:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadConfigurations = async () => {
    try {
      const response = await fetch('/api/configs');
      if (response.ok) {
        const data = await response.json();
        setConfigurations(data.configurations);
      }
    } catch (error) {
      console.error('Failed to load configurations:', error);
    }
  };

  const toggleRule = (ruleName: string) => {
    setRules(rules.map(rule => 
      rule.name === ruleName 
        ? { ...rule, enabled: !rule.enabled }
        : rule
    ));
  };

  const changeSeverity = (ruleName: string, severity: string) => {
    setRules(rules.map(rule => 
      rule.name === ruleName 
        ? { ...rule, severity }
        : rule
    ));
  };

  const saveConfiguration = async (name: string) => {
    if (!name.trim()) {
      alert('Please enter a configuration name');
      return;
    }

    setIsSaving(true);
    try {
      const configData = {
        rules: {
          ...rules.reduce((acc, rule) => {
            acc[rule.name] = {
              enabled: rule.enabled,
              severity_override: rule.severity !== 'default' ? rule.severity : null
            };
            return acc;
          }, {} as Record<string, any>)
        }
      };

      const formData = new FormData();
      formData.append('name', name);
      formData.append('config_data', JSON.stringify(configData));

      const response = await fetch('/api/config', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        alert('Configuration saved successfully!');
        loadConfigurations();
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch (error) {
      alert('Failed to save configuration: ' + error);
    } finally {
      setIsSaving(false);
    }
  };

  const loadConfiguration = async (name: string) => {
    try {
      const response = await fetch(`/api/config/${name}`);
      if (response.ok) {
        const config = await response.json();
        // Update rules based on loaded configuration
        setRules(rules.map(rule => ({
          ...rule,
          enabled: config.rules[rule.name]?.enabled ?? rule.enabled,
          severity: config.rules[rule.name]?.severity_override ?? 'default'
        })));
        setSelectedConfig(name);
      }
    } catch (error) {
      alert('Failed to load configuration: ' + error);
    }
  };

  if (isLoading) {
    return (
      <div className="results">
        <div className="loading">
          <Loader className="spinner" />
          <p>Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="results">
      <h3>
        <Settings className="inline-icon" />
        Rule Configuration
      </h3>

      {/* Saved Configurations */}
      <div className="mb-6">
        <h4>Saved Configurations</h4>
        {configurations.length > 0 ? (
          <div className="flex flex-wrap gap-2 mb-4">
            {configurations.map((config) => (
              <button
                key={config.name}
                className={`secondary ${selectedConfig === config.name ? 'active' : ''}`}
                onClick={() => loadConfiguration(config.name)}
              >
                {config.name} ({config.rules_count} rules)
              </button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No saved configurations</p>
        )}

        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Configuration name"
            id="config-name"
            className="flex-1 border rounded px-3 py-1"
          />
          <button
            onClick={() => {
              const name = (document.getElementById('config-name') as HTMLInputElement)?.value;
              if (name) saveConfiguration(name);
            }}
            disabled={isSaving}
          >
            <Save className="inline-icon" />
            {isSaving ? 'Saving...' : 'Save Config'}
          </button>
        </div>
      </div>

      {/* Rules */}
      <div>
        <h4>Available Rules</h4>
        <div className="space-y-3">
          {rules.map((rule) => (
            <div key={rule.name} className="border rounded p-3 bg-white">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    onChange={() => toggleRule(rule.name)}
                    className="mr-2"
                  />
                  <strong>{rule.name}</strong>
                </div>
                <select
                  value={rule.severity}
                  onChange={(e) => changeSeverity(rule.name, e.target.value)}
                  className="border rounded px-2 py-1 text-sm"
                >
                  <option value="default">Default</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                </select>
              </div>
              <p className="text-sm text-gray-600">{rule.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ConfigurationPanel;
