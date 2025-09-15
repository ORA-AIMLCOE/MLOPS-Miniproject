pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')
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
                    // Get short commit hash
                    def commitHash = bat(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "Commit hash: ${commitHash}"

                    // Build Docker image with clean tag
                    bat "docker build -t pothole-detection:${commitHash} ."
                }
            }
        }

        stage('Run Analysis') {
            steps {
                script {
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
