
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
    }
}
