import importlib.util
import pathlib
import unittest

from adk_agent.agent import find_best_job_match, infer_terraform_action, infer_direct_deployment_prompt


script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "jenkins_init_jobs_fixed.py"
spec = importlib.util.spec_from_file_location("jenkins_init_jobs_fixed", script_path)
jenkins_init_jobs_fixed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jenkins_init_jobs_fixed)


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

    def test_detects_legacy_duplicate_job_aliases(self):
        self.assertIn("Api-Healcheck", jenkins_init_jobs_fixed.get_legacy_job_names("API-Health-Check"))
        self.assertIn("Git-Repo-Clone", jenkins_init_jobs_fixed.get_legacy_job_names("Git-Repository-Clone"))
        self.assertIn("Yahoo-Scraper", jenkins_init_jobs_fixed.get_legacy_job_names("Yahoo-Stock-Scraper"))

    def test_infers_terraform_action_from_prompt(self):
        self.assertEqual(infer_terraform_action("deploy prometheus server"), "deploy")
        self.assertEqual(infer_terraform_action("destroy prometheus server"), "destroy")
        self.assertEqual(infer_terraform_action("remove prometheus"), "destroy")
        self.assertEqual(infer_terraform_action("destroy kubernetes grafana deployment"), "destroy")

    def test_matches_kubernetes_grafana_deploy_aliases(self):
        jobs = [
            "Prometheus-Server-Deploy",
            "Kubernetes-Grafana-Deploy",
        ]
        self.assertEqual(find_best_job_match("deploy kubernetes cluster with grafana", jobs), "Kubernetes-Grafana-Deploy")
        self.assertEqual(find_best_job_match("run grafana in a kind cluster", jobs), "Kubernetes-Grafana-Deploy")

    def test_matches_kubernetes_loki_deploy_aliases(self):
        jobs = [
            "Kubernetes-Grafana-Deploy",
            "Kubernetes-Loki-Deploy",
        ]
        self.assertEqual(find_best_job_match("deploy loki in kubernetes", jobs), "Kubernetes-Loki-Deploy")
        self.assertEqual(find_best_job_match("run loki and grafana in kind", jobs), "Kubernetes-Loki-Deploy")

    def test_infers_direct_loki_deployment_prompts(self):
        self.assertEqual(
            infer_direct_deployment_prompt("Could you deploy Loki on a kuberenetes cluster"),
            ("Kubernetes-Loki-Deploy", "deploy"),
        )
        self.assertEqual(
            infer_direct_deployment_prompt("Please destroy Loki"),
            ("Kubernetes-Loki-Deploy", "destroy"),
        )

    def test_infers_direct_ansible_observability_prompts(self):
        self.assertEqual(
            infer_direct_deployment_prompt("Use Ansible to scrape Ollama metrics with Prometheus"),
            ("Ansible-Prometheus-Metrics", "deploy"),
        )
        self.assertEqual(
            infer_direct_deployment_prompt("Create a Grafana dashboard for resource monitoring"),
            ("Ansible-Grafana-Dashboard", "deploy"),
        )
        self.assertEqual(
            infer_direct_deployment_prompt("Use Ansible and Promtail to collect Loki logs"),
            ("Ansible-Loki-Logs", "deploy"),
        )


if __name__ == "__main__":
    unittest.main()
