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
        stage('Health Check') {
            steps {
                sh 'echo "Checking API health..."'
                sh 'curl -I https://www.google.com || true'
                sh 'curl -I https://api.github.com || true'
            }
        }
    }
}''')

createPipeline("Yahoo-Stock-Scraper", "Fetch stock prices from Yahoo Finance", '''pipeline {
    agent any
    stages {
        stage('Fetch Stock') {
            steps {
                sh 'echo "Fetching stock data for AAPL..."'
                sh 'python3 -c "import yfinance as yf; stock = yf.Ticker(\\"AAPL\\"); print(stock.info[\\"currentPrice\\"])"'
            }
        }
    }
}''')

createPipeline("Git-Repository-Clone", "Clone a git repository", '''pipeline {
    agent any
    stages {
        stage('Clone') {
            steps {
                echo "Clone Repository Stage"
                sh 'echo "Configure this job with a git repository URL"'
            }
        }
    }
}''')

instance.save()
println "✓ All pipeline jobs initialized"
