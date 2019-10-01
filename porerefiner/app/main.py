from flask import Flask

app = Flask(__name__)




@app.route('/api/runs/<int:run_id>/attach', methods=['POST,'])
def attach_to_run(run_id): #TODO
    pass

@app.route('/api/runs/<int:run_id>', methods=['GET', 'POST', 'DELETE'])
def run_control(run_id): #TODO
    pass

@app.route('/api/runs/')
def list_runs(): #TODO
    pass

