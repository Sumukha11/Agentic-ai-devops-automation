pipeline {
    agent any

    parameters {
        string(name: 'GIT_REPO_URL', defaultValue: 'https://github.com/githubtraining/hellogitworld.git', description: 'Git repository URL to clone')
        string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Branch name to checkout')
        string(name: 'CLONE_DIR', defaultValue: '/tmp/cloned_repo', description: 'Destination directory for clone')
    }

    stages {
        stage('Clone Repository') {
            steps {
                script {
                    echo "Cloning ${params.GIT_REPO_URL} branch ${params.GIT_BRANCH} into ${params.CLONE_DIR}"
                    if (fileExists(params.CLONE_DIR)) {
                        sh "rm -rf ${params.CLONE_DIR}"
                    }
                    sh '''
                        if ! command -v git >/dev/null 2>&1; then
                            echo "Git is not installed. Attempting to install..."
                            apt-get update && apt-get install -y git
                        fi
                        git clone -b "${GIT_BRANCH}" "${GIT_REPO_URL}" "${CLONE_DIR}"
                    '''
                }
            }
        }
    }
}