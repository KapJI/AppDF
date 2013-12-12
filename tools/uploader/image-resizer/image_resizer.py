import os
import subprocess

def resize(input_path, output_path, width, height):
    # path to the `image_resizer` executable
    binary = os.path.abspath(os.path.join(os.path.dirname(__file__), 'image_resizer'))
    proc = subprocess.Popen([binary, input_path, output_path, str(width), str(height)],
                                    stdin  = subprocess.PIPE,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE)
    proc.wait()