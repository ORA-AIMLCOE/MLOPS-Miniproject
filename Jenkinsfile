pipeline {
    agent any

    triggers {
        pollSCM('* * * * *') // poll every minute
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
                    def commitHash = bat(
                        script: '@echo off && git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    echo "Building Docker image with tag: pothole-detection:${commitHash}"
                    bat "docker build -t pothole-detection:${commitHash} ."
                }
            }
        }
        
        stage('Run Analysis') {
            steps {
                script {
                    def commitHash = bat(
                        script: '@echo off && git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    echo "Running container pothole-detection:${commitHash}"
        
                    // Run container and mount workspace (Windows path needs quotes)
                    bat "docker run --rm -v \"%cd%:/workspace\" pothole-detection:${commitHash} python your_script.py --output /workspace/output.csv"
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
