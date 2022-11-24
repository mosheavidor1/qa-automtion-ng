import hudson.model.*


def stdout_list = []
def HARBOR_DOCKER_REGISTRY='dops-registry.fortinet-us.com'
def IMAGE_NAME="fedr/python3_nodejs"
def DOCKER_SHA256SUM=""
def JOB_TYPE=""


def get_index_of_os(os_name) {
    os_list = [
        "windows_11_64_bit", "windows_10_64_bit", "windows_10_32_bit",
        "windows_8_64_bit", "windows_8_32_bit", "windows_7_64_bit", "windows_7_32_bit",
        "windows_server_2016", "windows_server_2019", "centOS_6", "centOS_7", "centOS_8", "centOS_8_stream",
        "ubuntu_16", "ubuntu_18", "ubuntu_20"
    ]
    int index = 0
    for (index=0; index < os_list.size(); index++) {
        if (os_name == os_list[index]) {
            break
        }
    }
    println("${os_name} is in index #${index}")
    return index
}


def can_run_automation(collector_name, num_of_collectors, run_automation_on) {
    println("checking to run automation on ${collector_name} with ${num_of_collectors} collectors")
    index = get_index_of_os(collector_name)
    return num_of_collectors.toInteger() > 0 && run_automation_on.split(',')[index] == 'true'
}


def run_automation_build(branch_name, tests_discover_type, tests, collector_type, oti_base_version) {
    try {
        println("running automation on ${collector_type}")
        build job: 'forti_edr_automation', parameters: [
            string(name: 'branchName', value: "${branch_name}"),
            string(name:'management_host_ip', value: "${MANAGEMENT_HOST_IP}"),
            string(name:'tests_discover_type', value: "${tests_discover_type}"),
            string(name:'tests', value: "${tests}"),
            booleanParam(name:'retry_on_failure', value: true),
            string(name:'collector_type', value: "${collector_type}"),
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
            string(name:'default_organization', value: "${ORGANIZATION}"),
            string(name:'oti_base_version', value: "${oti_base_version}")
        ]
    } catch(Exception e) {
        println "Exception: ${e}"
        return false
    }
    return true
}


if (env.JOB_NAME.contains('by_automation')) {
    JOB_TYPE = 'direct'
}
else {
    JOB_TYPE = 'external'
}


generic_params = [
    [$class: 'WHideParameterDefinition',
        defaultValue: JOB_TYPE,
        name: 'deployment_method'],

    string( name: 'branchName',
            defaultValue: 'main',
            description: 'Environment creation branch'),

    choice( name: 'vsphere_cluster',
            choices: ['40', '30', '20', '10'],
            description: ''),

    string( name: 'environment_name',
            defaultValue: '',
            description: 'Desired environment name'),

    separator(name: "versions_separator"),

    string( name: 'management_version',
            defaultValue: '5.2.0.x',
            description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x'),

    string( name: 'aggregator_version',
            defaultValue: '5.2.0.x',
            description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x'),

    string( name: 'core_version',
            defaultValue: '5.2.0.x',
            description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x'),

    string( name: 'windows_collector_version',
            defaultValue: '5.2.0.x',
            description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x'),

    string( name: 'linux_collector_version',
            defaultValue: '5.2.0.x',
            description: 'insert the exact version or base version with .x as build number for latest build, for example 5.2.0.x'),
]

if (JOB_TYPE == 'direct') {
    components_params = [
        separator(name: "components_separator"),

        choice( name: 'managements_amount',
                choices: ['1', '2'],
                description: ''),

        [$class: 'DynamicReferenceParameter',
           choiceType: 'ET_FORMATTED_HTML',
           description: 'enter amount of aggregators and cores to each of the management machines. the number of aggregators is of dedicated machines, regardless to BOTH param',
           name: 'components',
           omitValueField: true,
           referencedParameters: 'managements_amount',
           script: [
               $class: 'GroovyScript',
               script: [
                   sandbox: true,
                   script: '''
int num = "${managements_amount}".toInteger()
html_to_be_rendered = "<table>"
for (int i=0; i < num; i++) {
  int indx = i + 1
  html_to_be_rendered = """
    ${html_to_be_rendered}
    <tr>
      <td>
        <label title="management #${indx}" class="">Management #${indx}: </label>
      </td>
      <td>
        <input class="" type="checkbox" name="value" id="deployment_architecture_${i}" checked >Both Management and Aggregator in the same machine</input> <br>
        <label class="" title="Aggregator Amount" >Aggregators Amount</label>
        <input class="" type="number" name="value" id="aggregators_amount_${i}" value="1"> <br>
        <label class="" title="Core Amount" >Cores Amount</label>
        <input class="" type="number" name="value" id="cores_amount_${i}" value="1"> <br>
      </td>
    </tr>
"""
}

html_to_be_rendered = "${html_to_be_rendered}</table>"

return html_to_be_rendered'''
                ]
            ]
        ]
    ]
}
else {
    components_params = [
        choice(name: 'management_and_aggregator_deployment_architecture',
               choices: ['both', 'separate'],
               description: 'choose deployment architecture'),

    //         separator(name: "components amount"),
        string( name: 'aggregators_amount',
                defaultValue: '1',
                description: 'can be higher than 1 in case of architecture is separate, else 1 will be the default'),

        string( name: 'cores_amount',
                defaultValue: '1',
                description: '')
    ]
}

collectors_params = [
    separator(name: "collectors_separator"),

    string( name: 'windows_11_64_bit',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_10_64_bit',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_10_32_bit',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_8_64_bit',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_8_32_bit',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_7_64_bit',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_7_32_bit',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_server_2016',
            defaultValue: '0',
            description: ''),

    string( name: 'windows_server_2019',
            defaultValue: '0',
            description: ''),

    string( name: 'centOS_6',
            defaultValue: '0',
            description: ''),

    string( name: 'centOS_7',
            defaultValue: '0',
            description: ''),

    string( name: 'centOS_8',
            defaultValue: '0',
            description: ''),

    string( name: 'centOS_8_stream',
            defaultValue: '0',
            description: ''),

    string( name: 'ubuntu_16',
            defaultValue: '0',
            description: ''),

    string( name: 'ubuntu_18',
            defaultValue: '0',
            description: ''),

    string( name: 'ubuntu_20',
            defaultValue: '0',
            description: '')
]

automation_params = [
    separator(name: "automation_separator"),

//     [$class: 'WHideParameterDefinition',
//         defaultValue: 'false',
//         description: 'Set true in order to run automation in parallel on all collectors that was created',
//         name: 'run_automation'],

    booleanParam( name: 'run_automation',
                  defaultValue: false,
                  description: 'Set true in order to run automation in parallel on all collectors that was created'),

    string( name: 'automation_branchName',
            defaultValue: 'main',
            description: 'Automation branch to run'),

    choice(name: 'tests_discover_type',
           choices: ['suite', 'keyword'],
           description: 'choose suite to run suite\\s of tests or keyword to run all tests including the keyword'),

    string( name: 'automation_tests',
            defaultValue: '',
            description: 'suites or tests to run according to given keyword'),

    string( name: 'oti_base_version',
            defaultValue: '5.1.0.590',
            description: 'base version that we are going to upgrade from'),

    [$class: 'DynamicReferenceParameter',
       choiceType: 'ET_FORMATTED_HTML',
       description: 'enter amount of aggregators and cores to each of the management machines. the number of aggregators is of dedicated machines, regardless to BOTH param',
       name: 'run_automation_on',
       omitValueField: true,
       referencedParameters: 'windows_11_64_bit,windows_10_64_bit,windows_10_32_bit,windows_8_64_bit,windows_8_32_bit,windows_7_64_bit,windows_7_32_bit,windows_server_2016,windows_server_2019,centOS_6,centOS_7,centOS_8,centOS_8_stream,ubuntu_16,ubuntu_18,ubuntu_20',
       script: [
           $class: 'GroovyScript',
           script: [
               sandbox: true,
               script: '''
collectors_data = [
    "windows_11_64_bit": "${windows_11_64_bit}".toInteger(),
    "windows_10_64_bit": "${windows_10_64_bit}".toInteger(),
    "windows_10_32_bit": "${windows_10_32_bit}".toInteger(),
    "windows_8_64_bit": "${windows_8_64_bit}".toInteger(),
    "windows_8_32_bit": "${windows_8_32_bit}".toInteger(),
    "windows_7_64_bit": "${windows_7_64_bit}".toInteger(),
    "windows_7_32_bit": "${windows_7_32_bit}".toInteger(),
    "windows_server_2016": "${windows_server_2016}".toInteger(),
    "windows_server_2019": "${windows_server_2019}".toInteger(),
    "centOS_6": "${centOS_6}".toInteger(),
    "centOS_7": "${centOS_7}".toInteger(),
    "centOS_8": "${centOS_8}".toInteger(),
    "centOS_8_stream": "${centOS_8_stream}".toInteger(),
    "ubuntu_16": "${ubuntu_16}".toInteger(),
    "ubuntu_18": "${ubuntu_18}".toInteger(),
    "ubuntu_20": "${ubuntu_20}".toInteger(),
]

html_to_be_rendered = "<table><tr>"

for (collector_data in collectors_data) {
  collector_name = collector_data.key
  hidden_attr = ''
  if (collector_data.value == 0) {
    hidden_attr = ' style="display:none"'
  }
  html_to_be_rendered = """
    ${html_to_be_rendered}
      <label tabindex="0" class="checkbox"${hidden_attr}>
        <input class="" type="checkbox" name="value" id="run_automation_controller_${collector_name}" >${collector_name}</input>
      </label>
  """
}

html_to_be_rendered = "${html_to_be_rendered}</tr></table>"

return html_to_be_rendered'''
           ]
       ]
   ]
]


properties([
    parameters(
        generic_params + components_params + collectors_params + automation_params
    )
])


pipeline {
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

                    if (JOB_TYPE == 'external') {
                        if (params.aggregators_amount.toInteger() < 1){
                            error "aggregator amount should be at least 1"
                        }

                        if (params.management_and_aggregator_deployment_architecture == "both" && params.aggregators_amount.toInteger() > 1){
                            error "aggregator amount should be 1 for *both* deployment architecture"
                        }
                    }
                    else {
                        if ("${env.run_automation}" == 'true' && "${env.automation_tests}" == '') {
                            error "must specify tests suite/keyword when running the automation"
                        }
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
                                        docker tag $IMAGE_NAME:$IMAGE_TAG $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM_$REQUIREMENTS_SHA256SUM
                                        docker push $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM_$REQUIREMENTS_SHA256SUM
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
                        env.REQUIREMENTS_SHA256SUM = REQUIREMENTS_SHA256SUM

                        sh  '''
                                docker run --volume $(pwd):/home/jenkins -w /home/jenkins --rm  --env-file ./myenv.txt -u $(id -u ${USER}):$(id -g ${USER}) $HARBOR_DOCKER_REGISTRY/$IMAGE_NAME:$DOCKER_SHA256SUM_$REQUIREMENTS_SHA256SUM ./run_test.sh
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
                    when {
                        expression { return can_run_automation("windows_11_64_bit", "${env.windows_11_64_bit}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WINDOWS_11_64", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows 10 64 bit"){
                    when {
                        expression { return can_run_automation("windows_10_64_bit", "${env.windows_10_64_bit}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WINDOWS_10_64", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows 10 32 bit"){
                    when {
                        expression { return can_run_automation("windows_10_32_bit", "${env.windows_10_32_bit}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WINDOWS_10_32", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows 8 64 bit"){
                    when {
                        expression { return can_run_automation("windows_8_64_bit", "${env.windows_8_64_bit}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WINDOWS_8_64", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows 8 32 bit"){
                    when {
                        expression { return can_run_automation("windows_8_32_bit", "${env.windows_8_32_bit}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WINDOWS_8_32", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows 7 64 bit"){
                    when {
                        expression { return can_run_automation("windows_7_64_bit", "${env.windows_7_64_bit}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WINDOWS_7_64", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows 7 32 bit"){
                    when {
                        expression { return can_run_automation("windows_7_32_bit", "${env.windows_7_32_bit}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WINDOWS_7_32", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows serve 2016"){
                    when {
                        expression { return can_run_automation("windows_server_2016", "${env.windows_server_2016}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WIN_SERVER_2016", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on windows server 2019"){
                    when {
                        expression { return can_run_automation("windows_server_2019", "${env.windows_server_2019}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "WIN_SERVER_2019", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on centos 6"){
                    when {
                        expression { return can_run_automation("centOS_6", "${env.centOS_6}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "LINUX_CENTOS_6", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on centos 7"){
                    when {
                        expression { return can_run_automation("centOS_7", "${env.centOS_7}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "LINUX_CENTOS_7", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on centos 8"){
                    when {
                        expression { return can_run_automation("centOS_8", "${env.centOS_8}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "LINUX_CENTOS_8", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on centos 8 Stream"){
                    when {
                        expression { return can_run_automation("centOS_8_stream", "${env.centOS_8_stream}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "LINUX_CENTOS_8_STREAM", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on ubuntu 16.04"){
                    when {
                        expression { return can_run_automation("ubuntu_16", "${env.ubuntu_16}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "LINUX_UBUNTU_16", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on ubuntu 18.04"){
                    when {
                        expression { return can_run_automation("ubuntu_18", "${env.ubuntu_18}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "LINUX_UBUNTU_18", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                stage ("Automation tests on ubuntu 20.04"){
                    when {
                        expression { return can_run_automation("ubuntu_20", "${env.ubuntu_20}", env.run_automation_on) }
                    }
                    steps {
                        script {
                            result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "LINUX_UBUNTU_20", env.oti_base_version)
                            if (!result) { currentBuild.result = 'FAILURE' }
                        }
                    }
                }

                // place holder for another OS types
                // stage ("Automation tests on "){
                //     when {
                //         expression { return can_run_automation("", "${env.}", env.run_automation_on) }
                //     }
                //     steps {
                //         script {
                //             result = run_automation_build(automation_branchName, env.tests_discover_type, env.automation_tests, "", env.oti_base_version)
                //             if (!result) { currentBuild.result = 'FAILURE' }
                //         }
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
