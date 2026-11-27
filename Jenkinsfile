
pipeline {
    agent any

    stages {

        // Stage 1: Install dependencies and run backend tests
        stage('Run Backend Tests') {
            steps {
                sh '''
                    python3 -m venv .venv

                    .venv/bin/pip install -r backend/requirements-dev.txt

                    .venv/bin/pytest -q backend/test_app.py
                '''
            }
        }

        // Stage 2: Build Docker images
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

        // Stage 3: Push images to Docker Hub
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

        // Stage 4: Test SSH connection to application EC2
        stage('Test App Server SSH') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'aws-app-ssh',
                    keyFileVariable: 'SSH_KEY',
                    usernameVariable: 'SSH_USER'
                )]) {
                    sh '''
                       ssh -vvv -i "$SSH_KEY" \
    -o StrictHostKeyChecking=accept-new \
    -o BatchMode=yes \
    -o ConnectTimeout=15 \
    -o ConnectionAttempts=1 \
    "$SSH_USER"@172.31.8.209 \
    "hostname"
                    '''
                }
            }
        }

        // Stage 5: Deploy to application EC2
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
