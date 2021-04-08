@Library('visenze-lib') _

pipeline {
  agent {
    label 'build'
  }

  options {
    disableConcurrentBuilds()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build') {
      steps {
        script {
          docker.withRegistry('', 'docker-hub-credential') {
            def tag = getVersion(env.BRANCH_NAME, env.GIT_COMMIT)
            sh "docker build -t visenze/slo-generator:${tag} ."
            def image = docker.image("visenze/slo-generator:${tag}")
            retry(2) {
              image.push()
            }
          }
        }
      }
    }

    stage('Deploy') {
      when {
        expression {
          return env.BRANCH_NAME == 'staging'
        }
      }

      steps {
        script {
          def extraValue = readYaml(file: "custom/helm-values.yaml")
          extraValue['image']['tag'] = getVersion(env.BRANCH_NAME, env.GIT_COMMIT)
          sh('rm -f values.yaml')
          writeYaml(file: 'values.yaml', data: extraValue)
          build(job: 'devops_helm_utility_deploy_charts',
              parameters: [string(name: 'ACTION', value: 'deploy'),
                           string(name: 'HELM_TIMEOUT', value: '300'),
                           booleanParam(name: 'HELM_WAIT', value: true),
                           string(name: 'RELEASE_NAME', value: "slo-generator"),
                           booleanParam(name: 'REUSE_VALUES', value: false),
                           string(name: 'NAMESPACE', value: 'sre'),
                           text(name: 'EXTRA_VALUES', value: readFile(file: 'values.yaml')),
                           string(name: 'CHART', value: 'visenze/simple-background-app'),
                           string(name: 'KUBECONFIG_CREDENTIAL_ID',
                                  value: 'eks_prod-online-ap-southeast-1_admin')])
        }
      }
    }
  }
}

def getVersion(branch, commit) {
  def version = readFile('version.txt').trim()
  if (branch != 'staging') {
    version = branch.replaceAll("/", "_")
  }
  version += "-" + commit.substring(0, 9)

  return version
}