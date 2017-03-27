import datetime
import requests
import time
import sys
import CHIP_IO.GPIO as GPIO

POLL_INTERVAL_SECONDS = 3
FAILED_JOB_COLORS = ['yellow', 'red']
PIN = "XIO-P4"
ON = GPIO.LOW
OFF = GPIO.HIGH
WORKDAY_START_TIME = datetime.time(8, 45)
WORKDAY_END_TIME = datetime.time(18, 0)

def during_working_hours():
    now = datetime.datetime.today()
    return now.weekday() in range(0,5) and WORKDAY_START_TIME < now.time() and now.time() < WORKDAY_END_TIME

def get_number_of_failed_jenkins_jobs(view_url):
    req = requests.get(view_url + '/api/json?tree=jobs[color]')
    if req.status_code != 200:
        print "Failed to get status of Jenkins jobs, returned status: {}, content:\n{}".format(req.status_code, req.text)
    
    job_results = [job for job in req.json()['jobs'] if job['color'] in FAILED_JOB_COLORS]
    return len(job_results)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        raise Exception("No Jenkins view URL passed. Usage: python jenkins-failed-build-warning-light.py http://jenkins.example.com/view/Main")
    
    view_url = sys.argv[1]
    print "Start monitoring Jenkins view {}".format(view_url)
    GPIO.cleanup()
    GPIO.setup(PIN, GPIO.OUT)
    current_state = OFF
    GPIO.output(PIN, current_state)
    try:
        while True:
            if during_working_hours():
                if get_number_of_failed_jenkins_jobs(view_url) == 0:
                    print "Everything is OK"
                    current_state = OFF
                else:
                    print "There are {} failing jobs".format()
                    current_state = ON
                GPIO.output(PIN, current_state)
            else:
                print "Nobody is in the office"
                if current_state == ON:
                    current_state = OFF
                    GPIO.output(PIN, current_state)
                
            time.sleep(POLL_INTERVAL_SECONDS)
    except (SystemExit, KeyboardInterrupt):
        GPIO.output(PIN, OFF)
        GPIO.cleanup()
