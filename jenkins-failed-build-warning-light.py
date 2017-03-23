import requests
import time
import sys
import CHIP_IO.GPIO as GPIO

POLL_INTERVAL_SECONDS = 3
FAILED_JOB_COLORS = ['yellow', 'red']
PIN = "XIO-P4"
ON = GPIO.LOW
OFF = GPIO.HIGH

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
    GPIO.cleanup()
    GPIO.setup(PIN, GPIO.OUT)
    try:
        while True:
            if get_number_of_failed_jenkins_jobs(view_url) == 0:
                GPIO.output(PIN, OFF)
            else:
                GPIO.output(PIN, ON)
            time.sleep(POLL_INTERVAL_SECONDS)
    except (SystemExit, KeyboardInterrupt):
        GPIO.output(PIN, OFF)
        GPIO.cleanup()
