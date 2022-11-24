# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
import json

from flask import Flask, request

# Flask constructor takes the name of
# current module (__name__) as argument.
from automation_services_utils.test_im_service_proxy.test_im_proxy_logic import TestImProxy

app = Flask(__name__)


# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.
@app.route('/startTestim', methods=['POST'])
def start_test_im():
    content = request.json

    testim_cmd = content.get('testim_cmd')
    params = content.get('params')
    test_timeout = content.get('test_timeout')

    status_code, output = TestImProxy.run_test(test_im_cmd=testim_cmd,
                                               data=params,
                                               test_timeout=test_timeout)

    response_msg = {
        'status_code': status_code,
        'output': output
    }
    response = app.response_class(
        response=json.dumps(response_msg),
        status=200,
        mimetype='application/json'
    )
    return response


# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0', port=5071)
