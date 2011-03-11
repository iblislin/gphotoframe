import os

def check_installed_in_path(command):
    path_dirs = []
    for d in os.environ['PATH'].split(':'):
        if os.path.isdir(d):
            path_dirs += os.listdir(d)

    return command in path_dirs

if __name__ == '__main__':
    command = 'f-spot'
    check_installed_in_path(command)
