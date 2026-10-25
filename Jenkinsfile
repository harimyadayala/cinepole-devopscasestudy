pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'dayalaharimya'          // <-- change this
        IMAGE_NAME     = "${DOCKERHUB_USER}/movie-booking"
        IMAGE_TAG      = "${env.BUILD_NUMBER}"
        DOCKER_CREDS   = credentials('dockerhub-creds')      // Username+password credential
        KUBECONFIG_CRED = 'kubeconfig'                       // Secret-file credential
    }

    triggers {
        githubPush()          // fires on GitHub webhook (push event)
        // pollSCM('* * * * *') // fallback if Jenkins is not publicly reachable
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    pytest -q
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh '''
                    echo "$DOCKER_CREDS_PSW" | docker login -u "$DOCKER_CREDS_USR" --password-stdin
                    docker push $IMAGE_NAME:$IMAGE_TAG
                    docker push $IMAGE_NAME:latest
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: "${KUBECONFIG_CRED}", variable: 'KUBECONFIG')]) {
                    sh '''
                        sed "s|IMAGE_PLACEHOLDER|$IMAGE_NAME:$IMAGE_TAG|g" k8s/deployment.yaml > k8s/deployment.rendered.yaml
                        kubectl apply -f k8s/deployment.rendered.yaml
                        kubectl apply -f k8s/service.yaml
                        kubectl rollout status deployment/movie-booking --timeout=120s
                        kubectl get pods,svc -l app=movie-booking
                    '''
                }
            }
        }
    }

    post {
        always  { sh 'docker logout || true' }
        success { echo "Deployed ${IMAGE_NAME}:${IMAGE_TAG} successfully." }
        failure { echo 'Pipeline failed - check the stage logs above.' }
    }
}
