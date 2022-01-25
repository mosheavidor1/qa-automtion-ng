import hudson.model.*


def stdout_list = []
def HARBOR_DOCKER_REGISTRY='dops-registry.fortinet-us.com'
def IMAGE_NAME="fedr/python3_nodejs"
def DOCKER_SHA256SUM=""

pipeline {
     
    parameters {
        string( name: 'branchName',
                defaultValue: 'main',
                description: 'Branch to build')	
        string( name: 'management_host_ip',
                defaultValue: '',
                description: 'Management Host IP')	               
        string( name: 'suite_name',
                defaultValue: '',
                description: 'Suite Name')	               
        string( name: 'single_test_name',
                defaultValue: '',
                description: 'Single Test Name')	               
        string( name: 'email_list',
                defaultValue: '',
                description: 'Email List')	               
    }
    agent { label 'cloud-agents' }
    stages {  

        stage('Checkout') {
            steps {
                script {
                    cleanWs()              
                    checkout scm    
                }
            }
        }      
        stage('Create Docker') {
            steps {
                script {

                    sh '[ -f ./myenv.txt ] && rm -f ./myenv.txt || echo "env file truncated"'  
                    params.each{
                        echo "Variable set $it.key = ${it.value}"
                        env."${it.key}" = it.value
                        sh "echo $it.key=${it.value} >> ./myenv.txt"
                    }
                    sh "echo BUILD_URL=${BUILD_URL} >> ./myenv.txt"
                    
                    step_out = ""
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
                            docker_exists = sh( script: '''
                                        echo $PASSWORD | docker login $HARBOR_DOCKER_REGISTRY  -u $USERNAME --password-stdin > /dev/null 2>&1
                                        echo $(docker inspect $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM  > /dev/null 2>&1 ; echo $?)
                                        ''', returnStdout: true ).trim()  
                            if ( docker_exists != "0" ) {
                                println("Start Building docker image")


                                step_out = sh(
                                            script:                            
                                            '''                                                
                                                echo $PASSWORD | docker login $HARBOR_DOCKER_REGISTRY  -u $USERNAME --password-stdin                                             
                                                docker image prune -a --force --filter "until=48h"
                                                docker build -t $IMAGE_NAME:$IMAGE_TAG  .
                                                docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                                                docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                                                docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:latest
                                                docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:latest    
                                                docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM
                                                docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM                                                           
                                            ''',
                                            returnStdout: true
                                            )  
                            }
                            else {
                                println("Docker image didn't change")
                            }                          
                        }                            
                        
                    } catch(Exception e) {
                        currentBuild.result = 'FAILURE'
                    } finally {
                        println ( step_out )
                    }                                      
                }
            }
        }      
        stage('Run Test') 
        {
            steps {
                script {
                    step_out = ""
                    try 
                    {

                    env.HARBOR_DOCKER_REGISTRY = HARBOR_DOCKER_REGISTRY             
                    env.IMAGE_NAME = IMAGE_NAME             
                    env.DOCKER_SHA256SUM = DOCKER_SHA256SUM             
                    
                    step_out = sh(
                                script:                            
                                '''                                                                                                                      
                                    docker run --volume $(pwd):/home/jenkins -w /home/jenkins --rm  --env-file ./myenv.txt -u $(id -u ${USER}):$(id -g ${USER}) $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM ./run_test.sh
                                ''',
                                returnStdout: true
                                )  
                                                 
                                             
                        
                    } catch(Exception e) {
                        currentBuild.result = 'FAILURE'
                    } finally {
                        println ( step_out )
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

                recipients=[ env.email_list ]

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