pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Frontend checks') {
            steps {
                dir('flask-app') {
                    sh 'python3 -m venv .venv'
                    sh '.venv/bin/python -m pip install -r requirements.txt'
                    sh '.venv/bin/python -m pytest -q'
                }
            }
        }

        stage('Backend checks') {
            steps {
                dir('java-backend') {
                    sh 'mvn -B test'
                }
            }
        }

        stage('Build Docker images') {
            steps {
                sh 'docker build -t pokedex-web:${BUILD_NUMBER} ./flask-app'
                sh 'docker build -t pokedex-backend:${BUILD_NUMBER} ./java-backend'
            }
        }
    }
}
