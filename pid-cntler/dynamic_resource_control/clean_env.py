import os

def clean_env():
    cmd = "docker ps -a | grep -E \'stream|specjbb\' | awk \'{print $1}\' | xargs docker rm -f"
    os.system(cmd)
    os.system('rm -rf specjbb2015log/*')
    os.system('pqos -R')
    os.system('rm -rf log/*')
    os.system('rm -rf redis_output/*')
    os.system('pkill -9 redis')

if __name__ == "__main__":
    clean_env()

