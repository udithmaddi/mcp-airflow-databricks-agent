import re
from typing import Dict, Any

class RCAEngine:
    """
    The Brain of the Operator.
    This class scans text logs for known error patterns (like OOM, Permissions, etc.)
    and suggests a fix.
    """
    def __init__(self):
        # Database of known errors (Regex Patterns)
        self.patterns = {
             "SchemaMismatch": [
                r"AnalysisException: cannot resolve",
                r"AnalysisException:.*column.*not found",
                r"Schema variance detected"
            ],
            "OOM": [ # Out Of Memory
                r"java.lang.OutOfMemoryError",
                r"Container killed by YARN for exceeding memory limits",
                r"ExecutorLostFailure",
                r"Total size of serialized results.*is bigger than"
            ],
            "Permissions": [
                r"AccessDeniedException",
                r"403 Forbidden",
                r"does not have permission"
            ],
            "DataQuality": [
                r"Constraint violation",
                r"NullPointerException.*input row"
            ],
            "Timeout": [
                r"TimeoutException",
                r"Heartbeat missing"
            ]
        }

    def analyze(self, log_text: str) -> Dict[str, Any]:
        """
        Main Function:
        Takes a big messy log, finds the needle in the haystack.
        """
        if not log_text:
            return {
                "root_cause": "Unknown",
                "confidence": "Low",
                "details": "No logs provided for analysis."
            }

        # Scan text against all known patterns
        for error_type, regex_list in self.patterns.items():
            for pattern in regex_list:
                match = re.search(pattern, log_text, re.IGNORECASE)
                if match:
                    # Found a match! Return the diagnosis.
                    return {
                        "root_cause": error_type,
                        "confidence": "High",
                        "evidence": match.group(0),
                        "recommendation": self._recommend(error_type)
                    }
        
        # If no patterns match
        return {
            "root_cause": "Unknown", 
            "confidence": "Low", 
            "details": "No specific error pattern matched. Manual review required."
        }

    def _recommend(self, error_type: str) -> str:
        """
        Returns a human-readable suggestion based on the error type.
        """
        recommendations = {
            "SchemaMismatch": "Check upstream schema changes. Update usage in Silver/Gold layers.",
            "OOM": "Increase cluster memory (scale up) or improve partitioning (repartition).",
            "Permissions": "Check Service Principal IAM roles.",
            "DataQuality": "Check for null primary keys or constraint violations.",
            "Timeout": "Check network connectivity or increase timeout settings."
        }
        return recommendations.get(error_type, "Investigate manually.")
