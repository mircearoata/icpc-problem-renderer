import argparse
import io
import re

from flask import Flask, request, send_file
import os
import subprocess
import tempfile
import zipfile

app = Flask(__name__)

problem2html_args = ['-b', '-c', '-H', '-m', '-q']

def backend_docker(input_dir_path: str, output_dir_path: str):
    return ['docker', 'run', '--rm', '-v', f'{os.path.abspath(input_dir_path)}:/data/in:ro', '-v', f'{os.path.abspath(output_dir_path)}:/data/out', 'problemtools/minimal', '/bin/problem2html', *problem2html_args, '-d', '/data/out', '/data/in']

def backend_local(input_dir_path: str, output_dir_path: str):
    return ['/bin/problem2html', *problem2html_args, '-d', output_dir_path, input_dir_path]

backend = backend_local

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    app.logger.info('Received a request: %s', file.filename)
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save the received file
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)

        app.logger.info('Saved the file to %s', file_path)

        input_dir_path = os.path.join(temp_dir, 'in')
        os.makedirs(input_dir_path, exist_ok=True)

        # Extract the zip file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(input_dir_path)

        app.logger.info('Extracted the file to %s', input_dir_path)

        # Execute the command with the input file as an argument
        output_dir_path = os.path.join(temp_dir, 'out')

        app.logger.info('Running the backend with input_dir_path=%s and output_dir_path=%s', input_dir_path, output_dir_path)

        command = backend(input_dir_path, output_dir_path)

        app.logger.info('Running the command: %s', ' '.join(command))

        subprocess.run(command, check=True)

        app.logger.info('Ran the command: %s', ' '.join(command))

        # Zip the output directory to memory bytes
        output_buffer = io.BytesIO()
        with zipfile.ZipFile(output_buffer, 'w') as zip_ref:
            for root, _, files in os.walk(output_dir_path):
                for file in files:
                    zip_ref.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), output_dir_path))

        app.logger.info('Zipped the output directory to memory bytes')

        output_buffer.seek(0)
        return send_file(output_buffer, as_attachment=True, download_name='problem.zip')


@app.route('/html2md', methods=['POST'])
def pandoc():
    # Read html input from request body
    html_input = request.data.decode('utf-8')
    app.logger.info('Received html2md request')

    # Run pandoc, piping stdin and stdout
    process = subprocess.Popen(['pandoc', '-f', 'html', '-t', 'markdown_strict+raw_tex'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=html_input.encode('utf-8'))
    if process.returncode != 0:
        app.logger.error('Pandoc error: %s', stderr.decode('utf-8'))
        return 'Error processing HTML', 500

    app.logger.info('Converted HTML to Markdown')

    markdown = stdout.decode('utf-8')

    markdown = re.sub(r'\$(.+?)\$', lambda x: '$' + re.sub(r'\\(.)', r'\1', x.group(1)) + '$', markdown, flags=re.DOTALL)

    # Return the markdown output
    return send_file(io.BytesIO(markdown.encode('utf-8')), as_attachment=True, download_name='output.md')


# WSGI
application = app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask app.')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to run the Flask app on.')
    parser.add_argument('-d', '--use-docker', action='store_true', help='Use Docker as the backend.')
    args = parser.parse_args()

    backend = backend_docker if args.use_docker else backend_local
    app.logger.setLevel('DEBUG')
    app.run(host='0.0.0.0', port=args.port)
