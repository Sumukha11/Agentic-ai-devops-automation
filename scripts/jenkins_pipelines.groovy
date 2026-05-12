import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition

def instance = Jenkins.getInstance()

def createPipeline(String name, String description, String script) {
    def job = instance.getItem(name)
    if (job == null) {
        def pipelineJob = instance.createProject(WorkflowJob, name)
        pipelineJob.setDescription(description)
        def flowDef = new CpsFlowDefinition(script, true)
        pipelineJob.setDefinition(flowDef)
        pipelineJob.save()
        println "✓ Created pipeline: ${name}"
    } else {
        println "✓ Pipeline exists: ${name}"
    }
}

createPipeline("API-Health-Check", "Check health of critical APIs", '''pipeline {
    agent any
    stages {
        stage('API Health Check') {
            steps {
                sh 'python3 << PYTHON_EOF
import requests
import time

services = {
    "Google": {"url": "https://www.google.com", "critical": True},
    "GitHub": {"url": "https://api.github.com", "critical": True},
    "Yahoo Finance": {"url": "https://query1.finance.yahoo.com", "critical": False}
}

def check_service(name, config):
    url = config["url"]
    critical = config["critical"]
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            print(f"{name}: {status}")
            if status >= 500:
                raise Exception(f"{name} server error")
            if name == "Yahoo Finance" and status == 429:
                print(f"{name}: Rate limited")
                return True
            return True
        except Exception as e:
            if attempt == 2:
                if critical:
                    print(f"{name} ERROR: {e}")
                    return False
                else:
                    print(f"{name} WARNING: {e}")
                    return True
            time.sleep(2)
    return True

all_ok = True
for name, config in services.items():
    if not check_service(name, config):
        all_ok = False

if not all_ok:
    print("Critical services failed")
    exit(1)

print("All critical services healthy")
PYTHON_EOF
'
            }
        }
    }
}''')

createPipeline("Yahoo-Stock-Scraper", "Fetch stock prices from Yahoo Finance", '''pipeline {
    agent any
    stages {
        stage('Fetch Stock Price') {
            steps {
                sh 'python3 << PYTHON_EOF
import yfinance as yf

stock = yf.Ticker("AAPL")
data = stock.history(period="1d")

if data.empty:
    print("No data found")
    exit(1)

price = data["Close"].iloc[-1]
print("Apple Stock Price: " + str(price))
PYTHON_EOF
'
            }
        }
    }
}''')

createPipeline("Git-Repository-Clone", "Clone a git repository", '''pipeline {
    agent any
    stages {
        stage('Clone Repository') {
            steps {
                echo "Cloning git repository..."
                sh '''
                    echo "Repository cloning stage"
                    echo "This job can be configured with a Git repository URL"
                '''
            }
        }
    }
}''')

instance.save()
println "✓ All pipeline jobs initialized"
