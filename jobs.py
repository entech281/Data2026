import schedule
import time
import threading
import pipeline
import logging

log = logging.getLogger("jobs.py")

JOB_INTERVAL_MINUTES = 5

def sync_from_tba():
    log.warning("Running  TBA Sync Job")
    pipeline.sync()
    log.warning("TBA sync job is complete")

#schedule.every(JOB_INTERVAL_MINUTES).minutes.do(sync_from_tba)
log.info(f"Scheduled Sync job every {JOB_INTERVAL_MINUTES} minutes")

def run_continuously(interval=10):
    """Continuously run, while executing pending jobs at each
    elapsed time interval.
    @return cease_continuous_run: threading. Event which can
    be set to cease continuous run. Please note that it is
    *intended behavior that run_continuously() does not run
    missed jobs*. For example, if you've registered a job that
    should run every minute and you set a continuous run
    interval of one hour then your job won't be run 60 times
    at each interval but only once.
    """
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run

#stop_run_continuously = run_continuously()

#def stop():
#    stop_run_continuously.set()