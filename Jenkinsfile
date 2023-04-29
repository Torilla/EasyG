pipeline {
    agent any

    stages {
        stage('Lint') {
            steps {
                sh "flake8 EasyG"
                sh "pylint EasyG"
            }
        stage('Test') {
            steps {
                sh "python3 tests/test_sssh.py"
            }
        }
    }
}
