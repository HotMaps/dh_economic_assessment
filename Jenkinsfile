node {
  stage('Init') {
    checkout scm
    sh 'cp /home/jenkins/hotmaps/gurobi.lic ./cm/gurobi_install/gurobi.lic'
  }
    
  stage('Build & Test') {
    try {
      sh 'docker-compose -f docker-compose.tests.yml -p hotmaps up --build --exit-code-from dh_economic_assessment'
    }
    finally {
      // stop services
      sh 'docker-compose -f docker-compose.tests.yml down' 
    }
  }
}
