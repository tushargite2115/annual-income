
pipeline {
    agent any

    stages {
        stage('Build Docker Images') {
            steps {
                sh '''
                    docker build \
                      -t tushargite2115/annual-income-backend:latest \
                      -t tushargite2115/annual-income-backend:${BUILD_NUMBER} \
                      ./backend

                    docker build \
                      -t tushargite2115/annual-income-frontend:latest \
                      -t tushargite2115/annual-income-frontend:${BUILD_NUMBER} \
                      ./frontend
                '''
            }
        }

        stage('Push Images to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKERHUB_USERNAME',
                    passwordVariable: 'DOCKERHUB_TOKEN'
                )]) {
                    sh '''
                        set +x
                        echo "$DOCKERHUB_TOKEN" | docker login \
                          -u "$DOCKERHUB_USERNAME" --password-stdin

                        docker push tushargite2115/annual-income-backend:latest
                        docker push tushargite2115/annual-income-backend:${BUILD_NUMBER}

                        docker push tushargite2115/annual-income-frontend:latest
                        docker push tushargite2115/annual-income-frontend:${BUILD_NUMBER}

                        docker logout
                    '''
                }
            }
        }

        stage('Test App Server SSH') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'aws-app-ssh',
                    keyFileVariable: 'SSH_KEY',
                    usernameVariable: 'SSH_USER'
                )]) {
                    sh '''
                        ssh -i "$SSH_KEY" \
                            -o StrictHostKeyChecking=accept-new \
                            "$SSH_USER"@172.31.8.209 \
                            "hostname"
                    '''
                }
            }
        }

        stage('Deploy to App EC2') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'aws-app-ssh',
                    keyFileVariable: 'SSH_KEY',
                    usernameVariable: 'SSH_USER'
                )]) {
                    sh '''
                        ssh -i "$SSH_KEY" \
                            -o StrictHostKeyChecking=accept-new \
                            "$SSH_USER"@172.31.8.209 \
                            'cd /home/ubuntu/annual-income && docker compose pull backend frontend && docker compose up -d backend frontend'
                    '''
                }
            }
        }
    }
}
