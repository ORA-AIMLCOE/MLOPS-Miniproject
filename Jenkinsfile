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
                    bat """
                        echo Running container ${IMAGE_NAME}:${IMAGE_TAG}
                        docker run --rm -v %cd%:/app ${IMAGE_NAME}:${IMAGE_TAG} python app.py
                    """
                }
            }
        }

        stage('Archive Results') {
            steps {
                script {
                    bat "dir" // Debug: list files so we know where output.csv is
                }
                archiveArtifacts artifacts: '**/output.csv', fingerprint: true
            }
        }
    }
}
