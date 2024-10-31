import os

def clean_env():
    cmd = "docker ps -a | grep -E \'stream|specjbb\' | awk \'{print $1}\' | xargs docker rm -f"
    os.system(cmd)
    os.system('rm -rf specjbb2015log/*')

if __name__ == "__main__":
    clean_env()

