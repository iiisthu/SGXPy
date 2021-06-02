import os
import sh
from os import path
import re
import time
import subprocess
import shlex
import signal

Parentdir = path.dirname(path.dirname(path.abspath(__file__)))
Collector = sh.Command(path.join(Parentdir, "sgxpython.py"))
ScriptDir = path.join(Parentdir, "script")

def getruncode(output):
    print("output:", output)
    starttip = "Now run: "
    for line in output.split('\n'):
        if starttip in line:
            runcode = line.split(starttip)[1]
            break
    return runcode

# Collect dependencies of the scriptfile and run it in Graphene
def runner(scriptfile, scriptargv, stdout = subprocess.PIPE):
    output = Collector(filter(None, [scriptfile] + scriptargv))
    olddir = os.getcwd()
    os.chdir(ScriptDir)
    rcode = shlex.split(getruncode(output))
    time.sleep(0.1)
    timeout = 100000
    run_times = 0
    times = 1
    while run_times < times:
        sleep_time = 0
        finish = False
        output = ""
        p = subprocess.Popen(rcode, stdout = stdout, preexec_fn=os.setsid)
        while sleep_time < timeout:
            time.sleep(0.001)
            if p.poll() is not None:
                finish = True
                break
            sleep_time += 1
        if finish:
            if stdout:
                output = p.stdout.read()
            break
        print("Timeout", run_times + 1)
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        run_times += 1

    if run_times == times:
        output = '=== Test failed === ' + ' '.join(rcode)
    os.chdir(olddir)
    return output

