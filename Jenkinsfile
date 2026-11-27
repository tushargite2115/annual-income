
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Backend Image') {
            steps {
                sh 'docker build -t annual-income-backend:jenkins ./backend'
            }
        }

        stage('Build Frontend Image') {
            steps {
                sh 'docker build -t annual-income-frontend:jenkins ./frontend'
            }
        }
    }
}
