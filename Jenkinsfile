pipeline {
    agent any

    stages {
        stage('Review') {
            environment { PATH = "${PATH}:/var/jenkins_home/.local/bin" }
            steps {
                sh "flake8 EasyG"
                sh "pylint EasyG"
            }
        }
    }
}
