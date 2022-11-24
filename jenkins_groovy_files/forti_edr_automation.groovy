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

        choice(name: 'tests_discover_type',
               choices: ['suite', 'keyword'],
               description: 'choose suite to run suite\\s of tests or keyword to run all tests including the keyword')

        string( name: 'tests',
                defaultValue: 'sanity',
                description: 'suites or tests to run according to given keyword')

        booleanParam(name: 'retry_on_failure',
                    defaultValue: false,
                    description: 're-run test in case of failure')

        choice(name: 'collector_type',
               choices: ['WINDOWS_11_64', 'WINDOWS_10_64', 'WINDOWS_10_32', 'WINDOWS_8_64',
               'WINDOWS_8_32', 'WINDOWS_7_64', 'WINDOWS_7_32',
               'WIN_SERVER_2016', 'WIN_SERVER_2019',
               'LINUX_CENTOS_6', 'LINUX_CENTOS_7', 'LINUX_CENTOS_8',
               'LINUX_UBUNTU_16', 'LINUX_UBUNTU_18', 'LINUX_UBUNTU_20'],
               description: 'choose collector type to run the tests on')

        booleanParam(name: 'report_results_to_jira',
                    defaultValue: false,
                    description: 'create test execution in jira and report tests results')

        string( name: 'email_list',
                defaultValue: '',
                description: 'Email List, comma delimiter')

        string( name: 'platfom_rest_branch',
                defaultValue: 'master',
                description: 'Platfom Rest Branch')

        string( name: 'testim_branch',
                defaultValue: 'master',
                description: 'branch to run from testim')

//         booleanParam(name: 'use_test_im_proxy',
//                     defaultValue: true,
//                     description: 'run testIM tests on proxy windows machine since they are not support running on linux')

        booleanParam(name: 'debug_mode',
                    defaultValue: true,
                    description: 'Set true for running the test with logs collection and snpashots functionality')

        booleanParam(name: 'register_to_fcs',
                    defaultValue: false,
                    description: 'Set true to register management to FCS - staging env')


        separator( name: 'upgrade_section')

        booleanParam(name: 'upgrade_management_to_latest_build',
                    defaultValue: false,
                    description: 'Set true in case you want to upgrade to latest build available')

        booleanParam(name: 'upgrade_aggregator_to_latest_build',
                    defaultValue: false,
                    description: 'Set true in case you want to upgrade to latest build available')

        booleanParam(name: 'upgrade_core_to_latest_build',
                    defaultValue: false,
                    description: 'Set true in case you want to upgrade to latest build available')

        booleanParam(name: 'upgrade_collector_to_latest_build',
                    defaultValue: false,
                    description: 'Set true in case you want to upgrade to latest build available')

        separator( name: 'setup_details_section')

//         string( name: 'management_ssh_user_name',
//                 defaultValue: 'root',
//                 description: '')
//
//         string( name: 'management_ssh_password',
//                 defaultValue: 'enSilo$$',
//                 description: '')

        string( name: 'rest_api_user',
                defaultValue: 'admin',
                description: '')

        string( name: 'rest_api_password',
                defaultValue: '12345678',
                description: '')

        string( name: 'registration_password',
                defaultValue: '12345678',
                description: '')

        string( name: 'default_organization',
                defaultValue: 'Default',
                description: '')

        separator( name: 'oti_params')

        string( name: 'oti_base_version',
                defaultValue: '5.1.0.590',
                description: 'base version that we are going to upgrade from')

    }
    triggers {
        parameterizedCron('''
            # leave spaces where you want them around the parameters. They'll be trimmed.
            # we let the build run with the default name


            # 5.2.1 environment
            # non - parallel
            #00 3 * * 0-5 % branchName=main; testim_branch=release/5.2.0.3; management_host_ip=; collector_type=WINDOWS_11_64; tests_discover_type=suite; tests=e2e_windows_collector_sanity; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=; upgrade_management_to_latest_build=True; upgrade_aggregator_to_latest_build=True; upgrade_core_to_latest_build=True; upgrade_collector_to_latest_build=True; retry_on_failure=False
            # parallel
            #00 3 * * 0-5 % branchName=main; testim_branch=release/5.2.0.3; management_host_ip=; collector_type=WINDOWS_11_64; tests_discover_type=suite; tests=e2e_windows_collector_sanity; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=; upgrade_management_to_latest_build=True; upgrade_aggregator_to_latest_build=True; upgrade_core_to_latest_build=True; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #00 3 * * 0-5 % branchName=main; testim_branch=release/5.2.0.3; management_host_ip=; collector_type=WINDOWS_11_64; tests_discover_type=suite; tests=e2e_windows_collector_sanity; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=; upgrade_management_to_latest_build=True; upgrade_aggregator_to_latest_build=True; upgrade_core_to_latest_build=True; upgrade_collector_to_latest_build=True; retry_on_failure=False

            # 6.0 environment
            # non - parallel
            00 19 * * * % branchName=main; testim_branch=master; management_host_ip=10.151.125.30; collector_type=WINDOWS_11_64; tests_discover_type=suite; tests=e2e_windows_collector_sanity; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=Jeep_non_parallel_new; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=False; retry_on_failure=False; register_to_fcs=False; oti_base_version=5.2.0.2406
            # parallel
            05 19 * * * % branchName=main; testim_branch=master; management_host_ip=10.151.125.61; collector_type=WINDOWS_10_64; tests_discover_type=suite; tests=e2e_windows_collector_sanity_parallel; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=Jeep_parallel_new; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=False; retry_on_failure=False; register_to_fcs=False; oti_base_version=5.2.0.2406
            10 19 * * * % branchName=main; testim_branch=master; management_host_ip=10.151.125.61; collector_type=WINDOWS_10_32; tests_discover_type=suite; tests=e2e_windows_collector_sanity_parallel; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=Jeep_parallel_new; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=False; retry_on_failure=False; register_to_fcs=False; oti_base_version=5.2.0.2406


            # MITRE 5.7.0
            00 03 * * * % branchName=main; testim_branch=master; management_host_ip=10.151.125.36; collector_type=WINDOWS_10_64; tests_discover_type=suite; tests=e2e_windows_collector_sanity; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=mitre_windows_10_64; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=False; retry_on_failure=False; register_to_fcs=False; oti_base_version=5.2.0.2406
            05 03 * * * % branchName=main; testim_branch=master; management_host_ip=10.151.125.83; collector_type=WIN_SERVER_2019; tests_discover_type=suite; tests=e2e_windows_collector_sanity; report_results_to_jira=True; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=MITRE_WIN_SERVER_19; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=False; retry_on_failure=False; register_to_fcs=False; oti_base_version=5.2.0.2406


            # edr events
            #00 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WINDOWS_11_64; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #05 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WINDOWS_10_64; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #10 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WINDOWS_10_32; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #15 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WINDOWS_8_64; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #20 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WINDOWS_8_32; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #25 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WINDOWS_7_64; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #30 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WINDOWS_7_32; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #35 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WIN_SERVER_2016; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            #40 8 * * 0-4 % branchName=main; testim_branch=master; management_host_ip=10.151.125.14; collector_type=WIN_SERVER_2019; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=enSiloCloudServices; rest_api_password=vjXddEa8tIhiPpWAaWu1NoJi; registration_password=dJRkpyx8kSxD2d28oNx5NzK3; default_organization=nightly_edr_event_tester; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False

            # edr events - MITRE
            05 8 * * * % branchName=main; testim_branch=master; management_host_ip=10.151.125.17; collector_type=WINDOWS_10_64; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=automation_mitre; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
            10 8 * * * % branchName=main; testim_branch=master; management_host_ip=10.151.125.17; collector_type=WIN_SERVER_2019; tests_discover_type=suite; tests=edr; report_results_to_jira=False; debug_mode=True; rest_api_user=admin; rest_api_password=user_P@ssword1!; registration_password=12345678; default_organization=automation_mitre; upgrade_management_to_latest_build=False; upgrade_aggregator_to_latest_build=False; upgrade_core_to_latest_build=False; upgrade_collector_to_latest_build=True; retry_on_failure=False
        ''')
    }
    options {
        timeout(time: 12, unit: 'HOURS')
    }
    agent {
      node {
        label 'cloud-agents'
        customWorkspace "/home/jenkins/workspace/forti_edr_automation/${env.BUILD_NUMBER}"
      }
    }
    stages {

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
                        env."${it.key}" = it.value
                        sh "echo $it.key=${it.value} >> ./myenv.txt"
                    }
                    sh "echo BUILD_URL=${BUILD_URL} >> ./myenv.txt"
                    sh "echo use_test_im_proxy=true >> ./myenv.txt"
                    sh "echo PYTHONTRACEMALLOC=1 >> ./myenv.txt"

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
                                docker ps -a
                            '''

                        sh  '''
                                docker run --volume $(pwd):/home/jenkins -w /home/jenkins --rm --cidfile ./cont_id.cid --env-file ./myenv.txt -u $(id -u ${USER}):$(id -g ${USER}) $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM ./run_test.sh
                            '''

                    } catch(Exception e) {
                        currentBuild.result = 'FAILURE'
                        println "Exception: ${e}"
                    } finally {
                        println "Stage $STAGE_NAME done"
//                         sh  '''
//                                 docker ps -a
//                             '''
//
//                         sh  '''
//                                cat ./cont_id.cid
//                             '''
//
//                         cid = readFile(file: './cont_id.cid').trim()
//                         short_cid = cid.substring(0, 12)
//
//                         println "cid: $cid"
//                         println "short_cid: $short_cid"
//                         docker_kill_cmd = "docker kill $short_cid"
//                         println "docker kill cmd: $docker_kill_cmd"
//                         sh  '''
//                                "${docker_kill_cmd}"
//                             '''
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
