# read test.yaml and post to the server

input_file = 'test.yaml'
url = 'http://localhost:8080/api/v1/semplify'
headers = {'Content-Type': 'application/x-yaml'}

with open(input_file, 'r') as file:
    data = file.read()
    