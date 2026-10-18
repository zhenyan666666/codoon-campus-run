#!/system/bin/sh
chmod 755 /data/local/tmp/run_route.sh
setsid /system/bin/sh /data/local/tmp/run_route.sh </dev/null >/dev/null 2>&1 &
sleep 2
echo started