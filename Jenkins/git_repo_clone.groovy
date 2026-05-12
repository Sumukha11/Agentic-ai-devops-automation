pipeline {
    agent any

    stages {
        stage('Clone Repository') {
            steps {
                sh '''
                python <<EOF
import subprocess
import os

# Example: clone a repository (you can parameterize this in Jenkins later)
repo_url = os.getenv("GIT_REPO_URL", "https://github.com/torvalds/linux.git")
clone_dir = "/tmp/cloned_repo"

if os.path.exists(clone_dir):
    print(f"Repository already exists at {clone_dir}. Pulling latest...")
    subprocess.run(["git", "-C", clone_dir, "pull"], check=True)
else:
    print(f"Cloning {repo_url} to {clone_dir}...")
    subprocess.run(["git", "clone", repo_url, clone_dir], check=True)

print("Clone successful!")
EOF
                '''
            }
        }
    }
}