import hudson.model.*


def stdout_list = []
def HARBOR_DOCKER_REGISTRY='dops-registry.fortinet-us.com'
def IMAGE_NAME="fedr/python3_nodejs"
def DOCKER_SHA256SUM=""


pipeline {

    parameters {
        string( name: 'branchName',
                defaultValue: 'main',
                description: 'Automation branch')

//         separator(name: "system components version")

        string( name: 'management_version',
                defaultValue: '5.2.0.x',
                description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x')

        string( name: 'aggregator_version',
                defaultValue: '5.2.0.x',
                description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x')

        string( name: 'core_version',
                defaultValue: '5.2.0.x',
                description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x')

        string( name: 'windows_collector_version',
                defaultValue: '5.2.0.x',
                description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x')

        string( name: 'linux_collector_version',
                defaultValue: '5.2.0.x',
                description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x')

//         separator(name: "deployment architecture")
        choice(name: 'management_and_aggregator_deployment_architecture',
               choices: ['both', 'separate'],
               description: 'choose deployment architecture')

//         separator(name: "components amount")
        string( name: 'aggregators_amount',
                defaultValue: '1',
                description: 'can be higher than 1 in case of architecture is separate, else 1 will be the default')

        string( name: 'cores_amount',
                defaultValue: '1',
                description: '')

        string( name: 'windows_11_64_bit',
                defaultValue: '0',
                description: '')

        string( name: 'windows_10_64_bit',
                defaultValue: '0',
                description: '')

        string( name: 'windows_10_32_bit',
                defaultValue: '0',
                description: '')

        string( name: 'windows_8_64_bit',
                defaultValue: '0',
                description: '')

        string( name: 'windows_8_32_bit',
                defaultValue: '0',
                description: '')

        string( name: 'windows_7_64_bit',
                defaultValue: '0',
                description: '')

        string( name: 'windows_7_32_bit',
                defaultValue: '0',
                description: '')

        string( name: 'windows_server_2016',
                defaultValue: '0',
                description: '')

        string( name: 'windows_server_2019',
                defaultValue: '0',
                description: '')

        string( name: 'centOS_6',
                defaultValue: '0',
                description: '')

        string( name: 'centOS_7',
                defaultValue: '0',
                description: '')

        string( name: 'centOS_8',
                defaultValue: '0',
                description: '')

        string( name: 'ubuntu_16',
                defaultValue: '0',
                description: '')

        string( name: 'ubuntu_18',
                defaultValue: '0',
                description: '')

        string( name: 'ubuntu_20',
                defaultValue: '0',
                description: '')
    }
    agent { 
      node {
        label 'cloud-agents' 
        customWorkspace "/home/jenkins/workspace/forti_edr_automation/${env.BUILD_NUMBER}"
      }
    }
    stages {

        stage('Params Check') {
            steps{
                script {

                    if (params.aggregators_amount.toInteger() < 1){
                        error "aggregator amount should be at least 1"
                    }

                    if (params.management_and_aggregator_deployment_architecture == "both" && params.aggregators_amount.toInteger() > 1){
                        error "aggregator amount should be 1 for *both* deployment architecture"
                    }

//                     if (params.management_version.matches("\\d+.\\d+.\\d+.\\w+")){
//                         error "Management: Incorrect version pattern"
//                     }
//
//                     if (params.management_and_aggregator_deployment_architecture == "separate" && params.aggregator_version.matches("\\d+.\\d+.\\d+.\\w+")){
//                         error "Aggregator: Incorrect version pattern"
//                     }
//
//                     if (params.core_version.matches("\\d+.\\d+.\\d+.\\w+")){
//                         error "Core: Incorrect version pattern"
//                     }
//
//                     if (params.windows_collector_version.matches("\\d+.\\d+.\\d+.\\w+")){
//                         error "Windows Collector: Incorrect version pattern"
//                     }
//
//                     if (params.linux_collector_version.matches("\\d+.\\d+.\\d+.\\w+")){
//                         error "Linux Collector: Incorrect version pattern"
//                     }
                }
            }
        }

        stage('Checkout') {
            steps {
                script {
                    cleanWs()              
                    checkout scm    
                    stdout_list.add("<div><h3><a href=\"${env.BUILD_URL}\">${env.BUILD_URL}</a></h3></div>")
                }
            }
        }      
        stage('Create Docker') {
            steps {
                script {
                    sh '[ -f ./myenv.txt ] && rm -f ./myenv.txt || echo "env file truncated"'
                    params.each{
                        echo "Variable set $it.key = ${it.value}"
                        env."${it.key}" = it.value.replace(" ", "_");
                        sh "echo $it.key=${it.value} >> ./myenv.txt"
                    }
                    sh "echo BUILD_URL=${BUILD_URL} >> ./myenv.txt"
                    sh "echo platfom_rest_branch=master >> ./myenv.txt"
                    sh "echo tests_discover_type=suite >> ./myenv.txt"
                    sh "echo tests=create_environment >> ./myenv.txt"
                    sh "echo report_results_to_jira=false >> ./myenv.txt"

                    try
                    {

                        withCredentials([sshUserPrivateKey(credentialsId: '3011e0c4-d9c2-4401-91b1-ae0808285370', keyFileVariable: 'KEYFILE')]) {
                                sh '''
                                    mkdir -p ./.ssh
                                    chmod 700 ./.ssh
                                    cp $KEYFILE ./.ssh/id_rsa
                                    chmod 600 ./.ssh/id_rsa
                                    echo "Host *\n  StrictHostKeyChecking no" > ./.ssh/config
                                '''
                        }
                        withCredentials([usernamePassword(credentialsId:'harbor_fortiedr_qa_automation', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')])
                        {
                            user = env.USERNAME
                            password = env.PASSWORD
                            env.IMAGE_TAG = env.BUILD_NUMBER ?: "latest"
                            env.IMAGE_NAME = IMAGE_NAME
                            env.HARBOR_DOCKER_REGISTRY =  HARBOR_DOCKER_REGISTRY

                            DOCKER_SHA256SUM = sh( script: "sha256sum Dockerfile | cut -d' ' -f1", returnStdout: true).trim()
                            env.DOCKER_SHA256SUM = DOCKER_SHA256SUM
                            REQUIREMENTS_SHA256SUM = sh( script: "sha256sum resources/requirements.txt | cut -d' ' -f1", returnStdout: true).trim()
                            env.REQUIREMENTS_SHA256SUM = REQUIREMENTS_SHA256SUM
                            docker_exists = sh( script: '''
                                        echo $PASSWORD | docker login $HARBOR_DOCKER_REGISTRY  -u $USERNAME --password-stdin > /dev/null 2>&1
                                        echo $(docker inspect $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM  > /dev/null 2>&1 ; echo $?)
                                        ''', returnStdout: true ).trim()
                            requirements_no_change = sh( script: '''
                                        echo $PASSWORD | docker login $HARBOR_DOCKER_REGISTRY  -u $USERNAME --password-stdin > /dev/null 2>&1
                                        echo $(docker inspect $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$REQUIREMENTS_SHA256SUM  > /dev/null 2>&1 ; echo $?)
                                        ''', returnStdout: true ).trim()
                            if ( docker_exists != "0" || requirements_no_change != "0" ) {
                                println("Start Building docker image")


                                sh '''
                                        echo $PASSWORD | docker login $HARBOR_DOCKER_REGISTRY  -u $USERNAME --password-stdin
                                        docker image prune -a --force --filter "until=48h"
                                        docker build -t $IMAGE_NAME:$IMAGE_TAG  .
                                        docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                                        docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                                        docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:latest
                                        docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:latest
                                        docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM
                                        docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM
                                        docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$REQUIREMENTS_SHA256SUM
                                        docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$REQUIREMENTS_SHA256SUM
                                    '''
                            }
                            else {
                                println("Docker image didn't change")
                            }
                        }

                    } catch(Exception e) {
                        println "Exception: ${e}"
                        currentBuild.result = 'FAILURE'
                    } finally {

                        println "Stage $STAGE_NAME done"

                    }
                }
            }
        }
        stage('Run Test')
        {
            steps {
                script {

                    try
                    {

                        env.HARBOR_DOCKER_REGISTRY = HARBOR_DOCKER_REGISTRY
                        env.IMAGE_NAME = IMAGE_NAME
                        env.DOCKER_SHA256SUM = DOCKER_SHA256SUM

                        sh  '''
                                docker run --volume $(pwd):/home/jenkins -w /home/jenkins --rm  --env-file ./myenv.txt -u $(id -u ${USER}):$(id -g ${USER}) $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM ./run_test.sh
                            '''



                    } catch(Exception e) {
                        currentBuild.result = 'FAILURE'
                        println "Exception: ${e}"
                    } finally {
                        println "Stage $STAGE_NAME done"
                    }
                }
            }
        }





    }
    post {
        always {
            script {
                allure([
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: './allure-results']]
                ])


                recipients= env.email_list.split( "[\\s,]+" )

                if ((env.TRIGGER_USER) && (env.TRIGGER_USER != "")){
                    recipients += env.TRIGGER_USER + "@ensilo.com"
                }

                emailext (
                    subject: "Job: ${env.JOB_NAME}, Build#: ${env.BUILD_NUMBER}, Status: ${currentBuild.result}",
                    body: stdout_list.join(''),
                    to: recipients.join(", "),
                    recipientProviders: [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']],
                )
			}
        }
    }
}
