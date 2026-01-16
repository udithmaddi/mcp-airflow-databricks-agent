import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PolicyGuardrails")

class PolicyGuardrails:
    """
    The Safety Net.
    This class prevents the AI from making dangerous mistakes.
    Example: "Don't restart a job 100 times" or "Don't restart if the table is deleted".
    """
    def __init__(self):
        # 1. Max Reruns: How many times can we try again? (Default: 2)
        self.max_reruns = int(os.getenv("MAX_RERUNS", "2"))
        
        # 2. Allowlist: Which pipelines are we allowed to touch?
        self.allowlist_dags = self._parse_list(os.getenv("ALLOWLIST_DAGS", ""))
        
        # 3. Blocked Actions: Things we NEVER do.
        self.blocked_actions = ["delete", "drop", "truncate"] 

    def _parse_list(self, env_str: str) -> List[str]:
        """Helper to turn a comma-separated string into a list."""
        if not env_str:
            return []
        return [item.strip() for item in env_str.split(",") if item.strip()]

    def is_dag_allowed(self, dag_id: str) -> bool:
        """
        Check: Is this pipeline in our 'Safe List'?
        If the list is empty, we default to blocking EVERYTHING for safety.
        """
        if not self.allowlist_dags:
            logger.warning("No allowlist configured. Defaulting to DENY ALL (Fail-Closed).")
            return False
        
        is_allowed = dag_id in self.allowlist_dags
        if not is_allowed:
            logger.warning(f"DAG '{dag_id}' blocked by allowlist.")
        return is_allowed

    def validate_rerun(self, dag_id: str, current_try_number: int, rca_root_cause: str) -> Dict:
        """
        The Main Decision Maker.
        Returns: { "allowed": True/False, "reason": "..." }
        """
        # Rule 1: Is it in the Allowlist?
        if not self.is_dag_allowed(dag_id):
            return {"allowed": False, "reason": f"DAG '{dag_id}' is not in the allowlist."}

        # Rule 2: Did we try too many times already?
        if current_try_number > self.max_reruns:
            return {
                "allowed": False, 
                "reason": f"Max reruns reached ({current_try_number} > {self.max_reruns})."
            }

        # Rule 3: Is the error fixed by a restart?
        # Some errors (like Bad Data) won't get fixed just by running again.
        unsafe_causes = ["SchemaMismatch", "Permissions", "DataQuality"]
        if rca_root_cause in unsafe_causes:
            return {
                "allowed": False,
                "reason": f"Root cause '{rca_root_cause}' requires manual intervention."
            }

        # All checks passed!
        logger.info(f"Rerun validated for {dag_id} (try {current_try_number}).")
        return {"allowed": True, "reason": "Safe to rerun."}

    def check_safety(self, tool_name: str, params: Dict) -> bool:
        """
        Extra check: Stop any tool that looks like it's deleting things.
        """
        if "delete" in tool_name.lower():
            return False
        return True
