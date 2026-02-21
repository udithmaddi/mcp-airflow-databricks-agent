from tools import generate_rca, rca
import json

# ==============================================================================
# 🏎️ TEST DRIVE SCRIPT
# This file lets us "Mock" detailed errors without waiting for a real pipeline to fail.
# It helps us prove that the "Brain" works, even if the "Body" (Databricks) is offline.
# ==============================================================================

def print_scenario(title, data):
    """Helper to make the output look nice."""
    print(f"\n{'='*20} {title} {'='*20}")
    print(json.dumps(data, indent=2))

def demo_scenario_1_schema_mismatch():
    """
    SCENARIO 1: The "Production" Path.
    Tests the whole chain: Airflow -> Databricks -> Logic.
    """
    print("\nRunning Scenario 1: Full Pipeline Diagnosis...")
    # NOTE: This connects to real systems, so it might fail if they are offline.
    result = generate_rca("gold_sales_daily", "run_2024_06_15")
    print_scenario("Scenario 1 Result", result)

def demo_scenario_2_oom():
    """
    SCENARIO 2: The "Offline" Path (Safer for Demo).
    We feed it a fake messy error log, and see if it can diagnose "Out Of Memory".
    """
    print("\nRunning Scenario 2: OOM Log Analysis...")
    
    # This is what a scary Java error looks like:
    oom_log = """
    2024-06-16 04:00:00 INFO TaskSetManager: Starting task 1.0 in stage 0.0
    2024-06-16 04:05:00 ERROR Executor: Exception in task 1.0 in stage 0.0
    java.lang.OutOfMemoryError: Java heap space
    at java.util.Arrays.copyOf(Arrays.java:3332)
    Container killed by YARN for exceeding memory limits. 5.5 GB of 5.5 GB physical memory used.
    """
    
    # We ask the Brain: "What is wrong here?"
    result = rca.analyze(oom_log)
    print_scenario("Scenario 2 Result", result)

if __name__ == "__main__":
    # Choose your adventure:
    demo_scenario_2_oom() # Use this for safe local demos
    # demo_scenario_1_schema_mismatch() # Use this only if fully connected
