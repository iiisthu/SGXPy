#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import sh
import logging
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import util

logging.basicConfig(format = '%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# elem: pid: (name, path, children pid)
ProcInfo = {}
# elem: pid, manifest object, issigned.
MFests = {}

def makeexec(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(path, mode)

def gennewfilename(name, nameset, sep = ""):
    if name not in nameset:
        return name
    i = 0
    n = name
    while n in nameset:
        i = i + 1
        n = name + sep + str(i)
    return n

def getnormalname(fullpath):
    return path.basename(fullpath).split(".")[0].replace("-", '_').replace('+', 'p')

class GenManifest:
    manifesttemplate = "python.manifest"

    def __init__(self, logfile, opts, pid = None):
        self.logfile = logfile
        if pid is None:
            self.pid = logfile.split('.')[-1]
        else:
            self.pid = pid
        ProcInfo[self.pid] = (None, None, [])
        self.opts = opts
        # The directory of the sgxpython script which has a script subdir to cache output
        self.filedir = path.abspath(path.dirname(__file__))
        # The Graphene Runtime directory
        self.runtimepath = path.join(opts.graphene, "Runtime")
        self.trusted_files = {
            "ld": "ld-linux-x86-64.so.2",
            "libc": "libc.so.6",
            "libdl": "libdl.so.2",
            "libm": "libm.so.6",
            "libpthread": "libpthread.so.0",
            "libutil": "libutil.so.1",
            "libresolv": "libresolv.so.2",
        }
        for key in self.trusted_files:
            self.trusted_files[key] = path.join(self.runtimepath, self.trusted_files[key])

        for trustedfile in opts.trust:
            name = getnormalname(trustedfile)
            name = gennewfilename(name, self.trusted_files)
            self.trusted_files[name] = trustedfile

        self.trusted_files["py_ascii"] = "/usr/lib/python2.7/encodings/ascii.py"
        self.trusted_files["pyc_ascii"] = "/usr/lib/python2.7/encodings/ascii.pyc"
        self.allowed_files = {"tmp": "/tmp"}
        for extrafile in opts.allow:
            name = getnormalname(extrafile)
            name = gennewfilename(name, self.allowed_files)
            self.allowed_files[name] = extrafile

        import getpass
        self.username = getpass.getuser()
        self.key = self.filedir + "/enclave-key.pem"
        # subprocess
        self.mount = {
            "/usr":"/usr",
            "/bin": "/bin",
            "/graphene": self.runtimepath,
            "/host": "/lib/x86_64-linux-gnu",
            "/tmp": "/tmp"
        }
        mroots = map(lambda mpoint: '/' + path.abspath(mpoint).split('/')[1], filter(None, sys.path))
        self.mount.update(dict(zip(*(mroots,mroots))))

    def genmanifest(self, mainscript = False):
        self.basename = ProcInfo[self.pid][0]
        self.manifestfile = path.join(self.opts.outdir, self.basename + ".manifest")
        with open(self.manifestfile, 'w') as f:
            f.write("#!%s SGX\n" % (path.join(self.runtimepath, "pal_loader")))
            loader = {
                "preload": "file:" + path.join(self.runtimepath, "libsysdb.so"),
                "env.LD_LIBRARY_PATH": "/graphene:/host:/usr/lib:/usr/lib/x86_64-linux-gnu",
                "env.PYTHONIOENCODING": "utf-8",
                "env.PATH": "/usr/bin:/bin",
                "env.USERNAME": self.username,
                "env.HOME": path.expanduser("~"),
                'env.PYTHONDONTWRITEBYTECODE': 1,
            }
            loader["execname"] = "file:" + ProcInfo[self.pid][0]
            loader["exec"] = "file:" + ProcInfo[self.pid][1]

            pythondir = path.dirname(sys.executable)
            if pythondir not in loader["env.PATH"].split(":"):
                loader["env.PATH"] = pythondir + ":" + loader["env.PATH"]
            for key in loader:
                f.write("loader.%s = %s\n" % (key, loader[key]))

            f.write("\n# mount point begin:\n")
            for key in self.mount:
                name = path.basename(key)
                f.write("fs.mount.%s.type = chroot\n" % name)
                f.write("fs.mount.%s.path = %s\n" % (name, key))
                f.write("fs.mount.%s.uri = file:%s\n" % (name, self.mount[key]))

            f.write("\n# script dependencies begin:\n")
            for key in self.trusted_files:
                # When reading and writing a file at the same time, only writable permission is set.
                if self.trusted_files[key] in self.allowed_files.values():
                    continue
                f.write("sgx.trusted_files.%s = file:%s\n" % (key, self.trusted_files[key]))

            for key in self.allowed_files:
                if self.allowed_files[key].startswith("/tmp/"):
                    continue
                f.write("sgx.allowed_files.%s = file:%s\n" % (key, self.allowed_files[key]))

            f.write("\n# miscellaneous \n")
            if mainscript:
                f.write("sgx.enclave_size = %s\n" % self.opts.mem)
            else:
                f.write("sgx.enclave_size = 512M\n")

            f.write("sgx.thread_num = %d\n" % self.opts.thread)
            f.write("loader.debug_type = %s \n" % ("inline" if self.opts.debug else "none"))
            f.write("loader.dbg_level = %s \n" % (self.opts.level))

            if self.opts.huge:
                f.write(
                        "sys.brk.size = 64M\n"
                        "glibc.heap_size = 4M\n")

            f.write("\n # subprocess \n")
            for k in ProcInfo[self.pid][2]:
                f.write("sgx.trusted_files.%s = file:%s\n" % (ProcInfo[k][0], ProcInfo[k][1]))
                f.write("sgx.trusted_children.%s = file:%s\n" % (ProcInfo[k][0], path.join(self.opts.outdir, ProcInfo[k][0] + ".sig")))

    def sign(self):
        sgxname = self.manifestfile + ".sgx"
        sh.python(path.join(self.filedir, "pal-sgx-sign"), "-libpal", self.runtimepath + "/libpal-Linux-SGX.so", "-key", self.key, "-output", sgxname, "-manifest", self.manifestfile, _err_to_out=True)
        logger.info("signing file ... " + sgxname)
        makeexec(sgxname)

    def gettoken(self):
        sh.python(path.join(self.filedir, "pal-sgx-get-token"), "-sig", path.join(self.opts.outdir, self.basename + ".sig"), "-output", path.join(self.opts.outdir, self.basename + ".token"), _err_to_out=True)
        logger.info("Got token file: " + self.basename + ".token")

    def extractdependency(self, fd = None):
        if fd is None:
            fd = open(self.logfile)
        for line in fd:
            line = line.strip()
            if line.endswith('ENOENT (No such file or directory)'):
                continue
            if line.startswith('execve("'):
                fullpath = line.split('"')[1]
                procnames = [ProcInfo[p][0] for p in ProcInfo]
                procname = gennewfilename(path.basename(fullpath), procnames)
                if ProcInfo[self.pid][0]:
                    pid = self.pid + "_1"
                    MFests[pid] = (GenManifest(self.logfile, self.opts, pid), False)
                    ProcInfo[pid] = (procname, fullpath, [])
                    ProcInfo[self.pid][2].append(pid)
                    return MFests[pid][0].extractdependency(fd)
                else:
                    ProcInfo[self.pid] = (procname, fullpath, [])
            # forked process
            elif line.startswith('clone('):
                # subprocess pid
                ProcInfo[self.pid][2].append(line.split(' = ')[1])
            elif line.startswith('openat('):
                fullpath, openflag= line.split('"')[1:]
                fullpath = path.abspath(fullpath)
                # Only regular file is supported.
                if not path.isfile(fullpath) or fullpath in self.trusted_files.values() or fullpath in  self.allowed_files.values():
                    continue

                # Replace special char in filename
                name = getnormalname(fullpath)
                # Extrace so file
                if ".so" in path.basename(fullpath):
                    if name not in self.trusted_files:
                        self.trusted_files[name] = fullpath
                else:
                    if 'O_CREAT|' in openflag:
                        name = gennewfilename(name, self.allowed_files)
                        self.allowed_files[name] = fullpath
                    else:
                        if fullpath.endswith(".py"):
                            name = "py_" + name
                        elif fullpath.endswith(".pyc"):
                            name = "pyc_" + name
                        name = gennewfilename(name, self.trusted_files)
                        self.trusted_files[name] = fullpath

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Collect all dependency files for a Python script.')
    parser.add_argument('--debug','-d', action='store_true', help='Output debug information')
    parser.add_argument('--sign', '-s', action='store_true', help='Sign without collecting operation')
    parser.add_argument('--level', '-l', type=int, default = 1, help='Debug level for PAL library OS')
    parser.add_argument('--outdir', '-o', default = None, help='Output directory for the manifest file')
    parser.add_argument('--mem', '-m', type = str, default = "256M", help='Memeory allocated to SGX')
    parser.add_argument('--thread', '-t', type = int, default = 16, help='Threads allocated to SGX')
    parser.add_argument('--graphene', '-g', type = str, default = "~/sgxpython/graphene", help = "The Graphene directory")
    parser.add_argument('--allow', '-a', default = [], nargs = "*", help = "Allowed files to read/write")
    parser.add_argument('--trust', '-b', default = [], nargs = "*", help = "Trusted files to read")
    parser.add_argument('--showoutput', '-w', action = 'store_true', help = "Show the ouput of scriptfile when tracing")
    parser.add_argument('--huge', '-u', action = 'store_true', help = "Allocate huge resource for the scriptfile")
    parser.add_argument('scriptfile')
    opts = parser.parse_known_args()
    opts, opts.extraarg = opts

    if opts.scriptfile.startswith('-m') or opts.scriptfile.endswith(".py"):
        # support -m to fix attempted relative import in non-package buf in numpy test cases
        if opts.scriptfile.endswith(".py"):
            opts.scriptfile = path.abspath(opts.scriptfile)
            if not path.exists(opts.scriptfile):
                logger.error("script file %s does not exists!", opts.scriptfile)
                exit()
        opts.extraarg.insert(0, opts.scriptfile)
        opts.scriptfile = sys.executable
    if not opts.outdir:
        opts.outdir = path.join(path.dirname(__file__), "script")
    if opts.mem.endswith("G"):
        opts.mem = "%dM" % (1024 * int(opts.mem[: -1]))
    if opts.huge:
        opts.thread = max(opts.thread, 12)
        opts.mem = "%dM" % (max(int(opts.mem[: -1]), 2048))
    opts.outdir = path.abspath(opts.outdir)
    opts.graphene = path.expanduser(opts.graphene)

    return opts

def getppid(pid):
    parpid = None
    for j in ProcInfo:
        if pid in ProcInfo[j][2] :
            parpid = j
            break
    return parpid

def signandgettoken(pid):
    # has been signed
    if MFests[pid][1]:
        return
    if ProcInfo[pid][2]:
        for k in ProcInfo[pid][2]:
            if not MFests[k][1]:
                signandgettoken(k)
                MFests[k] = (MFests[k][0], True)
    MFests[pid][0].sign()
    MFests[pid][0].gettoken()
    MFests[pid] = (MFests[pid][0], True)

# the info of child proc with pid is empty
def printproctree(pid, level = 0):
    print "    " * level + "+--", pid, ProcInfo[pid][0], ProcInfo[pid][1]
    for k in ProcInfo[pid][2]:
        printproctree(k, level + 1)

def migratesubproc(pid, ppid):
    # execved process
    if ProcInfo[pid][0]:
        return
    if ProcInfo[pid][2]:
        for k in ProcInfo[pid][2]:
            if ProcInfo[k][0] is None:
                migratesubproc(k, ppid)
        ProcInfo[ppid][2].append(ProcInfo[pid][2])
    MFests[ppid][0].trusted_files.update(MFests[pid][0].trusted_files)
    MFests[ppid][0].allowed_files.update(MFests[pid][0].allowed_files)
    ProcInfo[ppid][2].pop(ProcInfo[ppid][2].index(pid))
    del ProcInfo[pid]
    del MFests[pid]

def gendependency(mainscript, opts):
    import glob
    logbase =  path.join(opts.outdir, path.splitext(path.basename(mainscript))[0]+ ".log")
    logwild = logbase + "*"
    [sh.rm("-f", f) for f in glob.glob(logwild)]
    strace = sh.strace.bake("-ff", "-o", logbase)
    try:
        strace(opts.scriptfile, opts.extraarg, _err_to_out = opts.showoutput)
    except KeyboardInterrupt:
        sh.pkill('-f',' '.join([opts.scriptfile] + opts.extraarg))
    mainmanifest = None
    mainpid = None
    for logfile in sorted(glob.glob(logwild), key = path.basename):
        # the id of first log is the main procession
        g = GenManifest(logfile, opts)
        if not mainmanifest:
            mainmanifest = g
            mainpid = g.pid
        MFests[g.pid] = (g, False)
        g.extractdependency()

    for k in ProcInfo.keys():
        migratesubproc(k, getppid(k))

    logger.info("Process Tree:")
    printproctree(mainpid)

    for k in filter(lambda g: g != mainmanifest, MFests):
        MFests[k][0].genmanifest()
    mainmanifest.genmanifest(True)

    [signandgettoken(k) for k in ProcInfo]

    import pipes
    print "Now run:", " ".join(filter(None, [mainmanifest.manifestfile + ".sgx",
                                             ' '.join([pipes.quote(a) for a in opts.extraarg])]))

if __name__ == '__main__':
    opts = parse_args()
    gendependency(opts.scriptfile, opts)

