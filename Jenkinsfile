pipeline {
    agent any  // You can change to 'docker' agent later for containerized builds

    triggers {
        // Poll GitHub every 5 minutes for changes (you can replace with webhooks later)
        pollSCM('* * * * *') // every minute
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build Docker image with current commit hash as tag
                    def commitHash = bat(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    bat "docker build -t pothole-detection:${commitHash} ."
                }
            }
        }

        stage('Run Analysis') {
            steps {
                script {
                    // Run the container and execute app.py
                    def commitHash = bat(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    bat "docker run --rm pothole-detection:${commitHash}"
                }
            }
        }

        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'output.csv', fingerprint: true
            }
        }
    }
}
