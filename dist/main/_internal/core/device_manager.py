kernel = sdb.shell("uname -r")
memory = sdb.shell("cat /proc/meminfo")
storage = sdb.shell("df -h")