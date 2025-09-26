#!/usr/bin/env python3
"""
Performance Analysis Tool for Workday Extend Code Review Tool
Helps identify bottlenecks and optimize performance on slower machines.
"""

import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Tuple
import sys
from contextlib import contextmanager

# Import our analysis modules
from file_processing.processor import FileProcessor
from parser.app_parser import ModelParser
from parser.rules_engine import RulesEngine
from parser.config_manager import ConfigurationManager

class PerformanceProfiler:
    """Profiles different stages of the analysis pipeline."""
    
    def __init__(self):
        self.timings = {}
        self.memory_usage = {}
        self.cpu_usage = {}
        self.stage_start_time = None
        self.stage_start_memory = None
        
    @contextmanager
    def profile_stage(self, stage_name: str):
        """Context manager to profile a specific stage."""
        # Record start metrics
        self.stage_start_time = time.time()
        self.stage_start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Start CPU monitoring in background
        cpu_thread = threading.Thread(target=self._monitor_cpu, args=(stage_name,))
        cpu_thread.daemon = True
        cpu_thread.start()
        
        try:
            yield
        finally:
            # Record end metrics
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - self.stage_start_time
            memory_delta = end_memory - self.stage_start_memory
            
            self.timings[stage_name] = duration
            self.memory_usage[stage_name] = {
                'start': self.stage_start_memory,
                'end': end_memory,
                'delta': memory_delta
            }
            
            print(f"⏱️  {stage_name}: {duration:.2f}s (Memory: +{memory_delta:.1f}MB)")
    
    def _monitor_cpu(self, stage_name: str):
        """Monitor CPU usage during a stage."""
        cpu_samples = []
        start_time = time.time()
        
        while time.time() - start_time < 60:  # Monitor for up to 60 seconds
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_samples.append(cpu_percent)
            time.sleep(0.1)
        
        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            self.cpu_usage[stage_name] = {
                'avg': avg_cpu,
                'max': max_cpu,
                'samples': len(cpu_samples)
            }
    
    def print_summary(self):
        """Print a comprehensive performance summary."""
        print("\n" + "="*60)
        print("📊 PERFORMANCE ANALYSIS SUMMARY")
        print("="*60)
        
        total_time = sum(self.timings.values())
        print(f"\n🕐 Total Analysis Time: {total_time:.2f}s")
        
        print(f"\n📈 Stage Breakdown:")
        for stage, duration in sorted(self.timings.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_time) * 100
            print(f"  {stage}: {duration:.2f}s ({percentage:.1f}%)")
        
        print(f"\n💾 Memory Usage:")
        for stage, mem_info in self.memory_usage.items():
            print(f"  {stage}: {mem_info['start']:.1f}MB → {mem_info['end']:.1f}MB (Δ{mem_info['delta']:+.1f}MB)")
        
        print(f"\n🖥️  CPU Usage:")
        for stage, cpu_info in self.cpu_usage.items():
            print(f"  {stage}: Avg {cpu_info['avg']:.1f}%, Max {cpu_info['max']:.1f}%")
        
        # Identify bottlenecks
        print(f"\n🔍 Bottleneck Analysis:")
        slowest_stage = max(self.timings.items(), key=lambda x: x[1])
        print(f"  Slowest stage: {slowest_stage[0]} ({slowest_stage[1]:.2f}s)")
        
        if slowest_stage[1] > total_time * 0.4:  # If slowest stage is >40% of total time
            print(f"  ⚠️  {slowest_stage[0]} is a significant bottleneck!")
        
        # Memory recommendations
        max_memory = max(mem['end'] for mem in self.memory_usage.values())
        if max_memory > 1000:  # >1GB
            print(f"  ⚠️  High memory usage detected: {max_memory:.1f}MB")
            print(f"      Consider reducing parallel processing or file size limits")

def analyze_performance(zip_path: Path, config_name: str = "comprehensive"):
    """Run a complete performance analysis."""
    profiler = PerformanceProfiler()
    
    print(f"🚀 Starting performance analysis of {zip_path.name}")
    print(f"📋 Using configuration: {config_name}")
    print(f"💻 System: {psutil.cpu_count()} CPU cores, {psutil.virtual_memory().total / 1024**3:.1f}GB RAM")
    
    try:
        # Stage 1: File Processing
        with profiler.profile_stage("File Processing"):
            processor = FileProcessor()
            source_files_map = processor.process_zip_file(zip_path)
            print(f"  📁 Processed {len(source_files_map)} files")
        
        # Stage 2: Parsing
        with profiler.profile_stage("File Parsing"):
            parser = ModelParser()
            context = parser.parse_files(source_files_map)
            print(f"  📄 Parsed {len(context.pmds)} PMD files, {len(context.pods)} POD files, {len(context.scripts)} script files")
        
        # Stage 3: Configuration Loading
        with profiler.profile_stage("Configuration Loading"):
            config_manager = ConfigurationManager()
            config = config_manager.load_config(config_name)
            print(f"  ⚙️  Loaded {len(config.rules.__dict__)} rules")
        
        # Stage 4: Rules Engine Initialization
        with profiler.profile_stage("Rules Engine Init"):
            rules_engine = RulesEngine(config)
            print(f"  🔧 Initialized {len(rules_engine.rules)} rules")
        
        # Stage 5: Analysis Execution
        with profiler.profile_stage("Analysis Execution"):
            findings = list(rules_engine.run(context))
            print(f"  🔍 Found {len(findings)} issues")
        
        # Print summary
        profiler.print_summary()
        
        # Performance recommendations
        print_performance_recommendations(profiler, zip_path)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

def print_performance_recommendations(profiler: PerformanceProfiler, zip_path: Path):
    """Print specific performance optimization recommendations."""
    print(f"\n💡 OPTIMIZATION RECOMMENDATIONS")
    print("="*60)
    
    # File size recommendations
    file_size_mb = zip_path.stat().st_size / 1024 / 1024
    if file_size_mb > 50:
        print(f"📦 Large file detected ({file_size_mb:.1f}MB)")
        print(f"   • Consider splitting large applications into smaller modules")
        print(f"   • Use file size limits in FileProcessor config")
    
    # Memory recommendations
    max_memory = max(mem['end'] for mem in profiler.memory_usage.values())
    if max_memory > 500:
        print(f"💾 High memory usage ({max_memory:.1f}MB)")
        print(f"   • Reduce MAX_CONCURRENT_FILES in FileProcessorConfig")
        print(f"   • Consider processing files in smaller batches")
    
    # CPU recommendations
    if profiler.cpu_usage:
        avg_cpu = sum(cpu['avg'] for cpu in profiler.cpu_usage.values()) / len(profiler.cpu_usage)
        if avg_cpu < 50:
            print(f"🖥️  Low CPU utilization ({avg_cpu:.1f}%)")
            print(f"   • Increase parallel processing if memory allows")
            print(f"   • Consider using more CPU cores for file parsing")
    
    # Specific stage optimizations
    slowest_stage = max(profiler.timings.items(), key=lambda x: x[1])
    if "File Processing" in slowest_stage[0]:
        print(f"📁 File processing is slow ({slowest_stage[1]:.2f}s)")
        print(f"   • Increase CHUNK_SIZE in FileProcessorConfig")
        print(f"   • Use faster storage (SSD vs HDD)")
        print(f"   • Consider file extraction optimization")
    
    elif "Analysis Execution" in slowest_stage[0]:
        print(f"🔍 Analysis execution is slow ({slowest_stage[1]:.2f}s)")
        print(f"   • Disable unnecessary rules in configuration")
        print(f"   • Use rule-specific configurations for different use cases")
        print(f"   • Consider caching ASTs (already implemented)")
    
    elif "File Parsing" in slowest_stage[0]:
        print(f"📄 File parsing is slow ({slowest_stage[1]:.2f}s)")
        print(f"   • Reduce parallel parsing workers")
        print(f"   • Optimize PMD/POD parsing logic")
        print(f"   • Consider pre-filtering irrelevant files")

def create_optimized_config():
    """Create an optimized configuration for slower machines."""
    config = {
        "file_processing": {
            "max_file_size": 25 * 1024 * 1024,  # 25MB (reduced from 50MB)
            "max_zip_size": 200 * 1024 * 1024,  # 200MB (reduced from 500MB)
            "chunk_size": 4096,  # 4KB (reduced from 8KB)
            "max_concurrent_files": 5,  # Reduced from 10
            "encoding": "utf-8"
        },
        "rules": {
            "enabled_rules": [
                "ScriptNullSafetyRule",
                "ScriptVarUsageRule", 
                "ScriptMagicNumberRule",
                "ScriptStringConcatRule",
                "ScriptConsoleLogRule",
                "ScriptUnusedVariableRule",
                "ScriptUnusedFunctionRule",
                "PMDSecurityDomainRule",
                "WidgetIdRequiredRule"
            ],
            "disabled_rules": [
                "ScriptComplexityRule",  # CPU intensive
                "ScriptFunctionParameterCountRule",
                "ScriptLongFunctionRule", 
                "ScriptNestingLevelRule",
                "ScriptVerboseBooleanCheckRule",  # Less critical
                "ScriptEmptyFunctionRule",
                "ScriptUnusedFunctionParametersRule",
                "ScriptUnusedScriptIncludesRule"
            ]
        }
    }
    
    import json
    with open("optimized_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("📝 Created optimized_config.json for slower machines")
    print("   • Reduced file size limits")
    print("   • Fewer concurrent files")
    print("   • Disabled CPU-intensive rules")
    print("   • Focused on critical security and quality rules")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python performance_analyzer.py <zip_file> [config_name]")
        print("Example: python performance_analyzer.py sampleProject.zip")
        sys.exit(1)
    
    zip_path = Path(sys.argv[1])
    config_name = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    
    if not zip_path.exists():
        print(f"❌ File not found: {zip_path}")
        sys.exit(1)
    
    # Create optimized config
    create_optimized_config()
    
    # Run analysis
    analyze_performance(zip_path, config_name)
