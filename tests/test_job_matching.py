import unittest
from adk_agent.agent import find_best_job_match


class TestJobMatching(unittest.TestCase):
    def test_matches_health_check_aliases(self):
        jobs = ["API-Health-Check", "Git-Repository-Clone", "Yahoo-Stock-Scraper"]
        self.assertEqual(find_best_job_match("Trigger Api-Healcheck", jobs), "API-Health-Check")
        self.assertEqual(find_best_job_match("api health check", jobs), "API-Health-Check")

    def test_matches_prometheus_deploy_aliases(self):
        jobs = [
            "API-Health-Check",
            "Git-Repository-Clone",
            "Yahoo-Stock-Scraper",
            "Prometheus-Server-Deploy",
        ]
        self.assertEqual(find_best_job_match("deploy prometheus server", jobs), "Prometheus-Server-Deploy")
        self.assertEqual(find_best_job_match("run terraform prometheus deployment", jobs), "Prometheus-Server-Deploy")


if __name__ == "__main__":
    unittest.main()
