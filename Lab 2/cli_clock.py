from time import strftime, sleep
while True:
    print (strftime("%m/%d/%Y %H:%M:%S"), end="", flush=True)
    print("\r", end="", flush=True)
    cmd = "curl -s wttr.in/?format=2"
    print(subprocess.check_output(cmd, shell=True).decode("utf-8"))
    sleep(1)
