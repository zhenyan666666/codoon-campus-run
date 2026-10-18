#!/system/bin/sh
F=/data/local/tmp/route_samples.txt
LOG=/data/local/tmp/route_run.log
STOP=/data/local/tmp/route_stop
rm -f $STOP
i=0
echo "START $(date +%H:%M:%S)" > $LOG
while read line; do
  if [ -f $STOP ]; then echo "STOPPED at $i $(date +%H:%M:%S)" >> $LOG; exit 0; fi
  cmd location providers set-test-provider-location gps --location "$line" --accuracy 5 >/dev/null 2>&1
  cmd location providers set-test-provider-location network --location "$line" --accuracy 5 >/dev/null 2>&1
  i=$((i+1))
  if [ $((i % 30)) -eq 0 ]; then echo "$(date +%H:%M:%S) idx=$i $line" >> $LOG; fi
  sleep 0.95
done < $F
echo "DONE $i $(date +%H:%M:%S)" >> $LOG