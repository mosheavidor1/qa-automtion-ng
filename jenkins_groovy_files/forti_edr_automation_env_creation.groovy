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

        booleanParam( name: 'run_automation',
                    defaultValue: false,
                    description: 'Set true in order to run automation in parallel on all collectors that was created')

        string( name: 'environment_name',
                defaultValue: '',
                description: 'Desired environment name')

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

//         string( name: 'centOS_6',
//                 defaultValue: '0',
//                 description: '')

        string( name: 'centOS_7',
                defaultValue: '0',
                description: '')

//         string( name: 'centOS_8',
//                 defaultValue: '0',
//                 description: '')

//         string( name: 'ubuntu_16',
//                 defaultValue: '0',
//                 description: '')

//         string( name: 'ubuntu_18',
//                 defaultValue: '0',
//                 description: '')

//         string( name: 'ubuntu_20',
//                 defaultValue: '0',
//                 description: '')

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
                        env."${it.key}" = "${it.value}".replace(" ", "_");
                        sh "echo $it.key=${it.value} >> ./myenv.txt"
                    }
                    sh "echo BUILD_URL=${BUILD_URL} >> ./myenv.txt"
                    sh "echo platfom_rest_branch=master >> ./myenv.txt"
                    sh "echo tests_discover_type=suite >> ./myenv.txt"
                    sh "echo tests=create_environment >> ./myenv.txt"
                    sh "echo report_results_to_jira=false >> ./myenv.txt"
                    sh "echo deployment_method=direct >> ./myenv.txt"

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

                        def envs = sh(returnStdout: true, script: 'env').split('\n')
                        envs.each { name  ->
                            println "Name: $name"
                        }
                    }
                }
            }
        }


        stage('Set updated environment variables from myenv.txt file'){
            steps{

                script {

                    // reading myenv.txt file which the automation updates during environment creation with new env details
                    // and set all new details as environment details
                    def file = readFile('./myenv.txt')
                    file.split('\n').each {envLine ->
                        def (key, value) = envLine.tokenize('=')
                        echo "${key} = ${value}"
                        env."${key}" = "${value}"
                    }
                    println("MANAGEMENT_HOST_IP = ${MANAGEMENT_HOST_IP}")
                }
            }
        }

        stage('Trigger automation job on environment'){
            when { expression { return "${env.run_automation}" == 'true'} }

            parallel {

                stage ("Automation tests on windows 11 64 bit"){
                    when { expression { return "${env.windows_11_64_bit}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WINDOWS_11_64'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows 10 64 bit"){
                    when { expression { return "${env.windows_10_64_bit}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WINDOWS_10_64'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows 10 32 bit"){
                    when { expression { return "${env.windows_10_32_bit}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WINDOWS_10_32'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows 8 64 bit"){
                    when { expression { return "${env.windows_8_64_bit}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WINDOWS_8_64'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows 8 32 bit"){
                    when { expression { return "${env.windows_8_32_bit}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WINDOWS_8_32'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows 7 64 bit"){
                    when { expression { return "${env.windows_7_64_bit}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WINDOWS_7_64'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows 7 32 bit"){
                    when { expression { return "${env.windows_7_32_bit}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WINDOWS_7_32'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows serve 2016"){
                    when { expression { return "${env.windows_server_2016}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WIN_SERVER_2016'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on windows server 2019"){
                    when { expression { return "${env.windows_server_2019}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'WIN_SERVER_2019'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                stage ("Automation tests on centos 7"){
                    when { expression { return "${env.centOS_7}".toInteger() > 0} }
                    steps{
                        build job: 'forti_edr_automation', parameters: [
                            string(name: 'branchName', value: "${branchName}"),
                            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                            string(name:'tests_discover_type', value: 'suite'),
                            string(name:'tests', value: 'sanity'),
                            booleanParam(name:'retry_on_failure', value: true),
                            string(name:'collector_type', value: 'LINUX_CENTOS_7'),
                            booleanParam(name:'report_results_to_jira', value: false),
                            string(name:'email_list', value: ''),
                            string(name:'platfom_rest_branch', value: 'master'),
                            string(name:'testim_branch', value: 'master'),
                            booleanParam(name:'use_test_im_proxy', value: true),
                            booleanParam(name:'debug_mode', value: true),
                            booleanParam(name:'upgrade_management_to_latest_build', value: false),
                            booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                            booleanParam(name:'upgrade_core_to_latest_build', value: false),
                            booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                            string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                            string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                            string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                            string(name:'default_organization', value: "${ORGANIZATION}")
                        ]
                    }
                }

                // place holder for another OS types
                // stage ("Automation tests on "){
                //     when { expression { return "${env.}".toInteger() > 0} }
                //     steps{
                //         build job: 'forti_edr_automation', parameters: [
                //             string(name: 'branchName', value: "${branchName}"),
                //             string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
                //             string(name:'tests_discover_type', value: 'suite'),
                //             string(name:'tests', value: 'sanity'),
                //             booleanParam(name:'retry_on_failure', value: true),
                //             string(name:'collector_type', value: 'WINDOWS_11_64'),
                //             booleanParam(name:'report_results_to_jira', value: false),
                //             string(name:'email_list', value: ''),
                //             string(name:'platfom_rest_branch', value: 'master'),
                //             string(name:'testim_branch', value: 'master'),
                //             booleanParam(name:'use_test_im_proxy', value: true),
                //             booleanParam(name:'debug_mode', value: true),
                //             booleanParam(name:'upgrade_management_to_latest_build', value: false),
                //             booleanParam(name:'upgrade_aggregator_to_latest_build', value: false),
                //             booleanParam(name:'upgrade_core_to_latest_build', value: false),
                //             booleanParam(name:'upgrade_collector_to_latest_build', value: false),
                //             string(name:'rest_api_user', value: "${ADMIN_REST_API_USER}"),
                //             string(name:'rest_api_password', value: "${ADMIN_REST_API_PASSWORD}"),
                //             string(name:'registration_password', value: "${DEFAULT_REGISTRATION_PASSWORD}"),
                //             string(name:'default_organization', value: "${ORGANIZATION}")
                //         ]
                //     }
                // }

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

                // recipients= env.email_list.split( "[\\s,]+" )

                // if ((env.TRIGGER_USER) && (env.TRIGGER_USER != "")){
                //     recipients += env.TRIGGER_USER + "@ensilo.com"
                // }

                // emailext (
                //     subject: "Job: ${env.JOB_NAME}, Build#: ${env.BUILD_NUMBER}, Status: ${currentBuild.result}",
                //     body: stdout_list.join(''),
                //     to: recipients.join(", "),
                //     recipientProviders: [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']],
                // )
            }
        }
    }
}
