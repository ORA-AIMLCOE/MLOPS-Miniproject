pipeline {
    agent any

    triggers {
        pollSCM('* * * * *') // poll every minute
    }

    environment {
        IMAGE_NAME = "pothole-detection"
        IMAGE_TAG  = "${env.BUILD_NUMBER}" 
        MLFLOW_TRACKING_URI = "http://localhost:5000"  
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
                        docker run --rm ^
                            -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} ^
                            -v "%cd%:/app" ^
                            -v "%cd%/mlruns:/app/mlruns" ^
                            -w /app ${IMAGE_NAME}:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'output.csv', onlyIfSuccessful: true
                archiveArtifacts artifacts: 'mlruns/**', onlyIfSuccessful: true
            }
        }
    }
}
