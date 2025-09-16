pipeline {
    agent any

    triggers {
        pollSCM('* * * * *') // poll every minute
    }

    environment {
        IMAGE_NAME = "pothole-detection"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"   // unique per build
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
                    bat """
                        docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    """
                }
            }
        }
        
        stage('Run Analysis') {
            steps {
                script {
                    bat """
                        echo Running container ${IMAGE_NAME}:${IMAGE_TAG}
                        docker run --rm -v %cd%:/app ${IMAGE_NAME}:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'output.csv', onlyIfSuccessful: true
            }
        }
    }
}
