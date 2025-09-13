export interface Finding {
  rule_id: string;
  severity: 'SEVERE' | 'WARNING' | 'INFO' | 'HINT';
  message: string;
  file_path: string;
  line: number;
  column?: number;
}

export interface AnalysisResult {
  findings: Finding[];
  total_files: number;
  total_rules: number;
  zip_filename: string;
  config_used?: string;
  timestamp: string;
}

export interface Rule {
  name: string;
  enabled: boolean;
  severity: string;
  description: string;
}

export interface Configuration {
  name: string;
  rules_count: number;
  created: number;
}
