from tools import generate_rca, rca
import json

def print_scenario(title, data):
    print(f"\n{'='*20} {title} {'='*20}")
    print(json.dumps(data, indent=2))

def demo_scenario_1_schema_mismatch():
    """
    Scenario 1: Full Pipeline Diagnosis via 'generate_rca' tool.
    Note: This requires valid Mock Mode or Real Credentials in tools.py/clients.
    """
    print("\nRunning Scenario 1: Full Pipeline Diagnosis...")
    # These IDs are examples; they will return 404s if running against real APIs without real IDs.
    # But checks the code path.
    result = generate_rca("gold_sales_daily", "run_2024_06_15")
    print_scenario("Scenario 1 Result", result)

def demo_scenario_2_oom():
    """
    Scenario 2: Independent RCA Engine Test.
    Does not require API access.
    """
    print("\nRunning Scenario 2: OOM Log Analysis...")
    
    oom_log = """
    2024-06-16 04:00:00 INFO TaskSetManager: Starting task 1.0 in stage 0.0
    2024-06-16 04:05:00 ERROR Executor: Exception in task 1.0 in stage 0.0
    java.lang.OutOfMemoryError: Java heap space
    at java.util.Arrays.copyOf(Arrays.java:3332)
    Container killed by YARN for exceeding memory limits. 5.5 GB of 5.5 GB physical memory used.
    """
    
    result = rca.analyze(oom_log)
    print_scenario("Scenario 2 Result", result)

if __name__ == "__main__":
    demo_scenario_2_oom() # Run local logic test only to avoid connection errors
    # demo_scenario_1_schema_mismatch() # Uncomment to test API integrations
