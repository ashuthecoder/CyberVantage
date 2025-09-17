"""
Test script to verify enhanced API logging with source tracking
"""
import os
import sys
from pyFunctions.api_logging import log_api_request, get_api_stats, get_api_source_stats

# Test logging functions
print("Testing API logging enhancements...")

# Log some test requests
log_api_request("test_azure_function", 100, True, 50, model_used="gpt-4", api_source="AZURE")
log_api_request("test_gemini_function", 120, True, 60, model_used="gemini-pro", api_source="GEMINI")
log_api_request("test_error_function", 80, False, error="Test error", api_source="AZURE")
log_api_request("test_system_function", 0, True, 10, api_source="SYSTEM")

# Get overall stats
print("\n=== Overall API Stats ===")
stats = get_api_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"By source: {stats.get('by_source', {})}")

# Get source-specific stats
print("\n=== Azure API Stats ===")
azure_stats = get_api_source_stats(source="AZURE")
print(f"Azure requests: {azure_stats['total_requests']}")
print(f"Success rate: {azure_stats['success_rate']}%")

print("\n=== Gemini API Stats ===")
gemini_stats = get_api_source_stats(source="GEMINI")
print(f"Gemini requests: {gemini_stats['total_requests']}")
print(f"Success rate: {gemini_stats['success_rate']}%")

print("\nAPI logging enhancements test completed")