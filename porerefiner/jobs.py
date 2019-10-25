from porerefiner.models import Job, File

import logging

async def poll_active_job(job):
    pass

async def submit_job(job):
    return 1

async def complete_job(job):
    return 1

async def poll_jobs():
    jobs_polled = 0
    jobs_submitted = 0
    jobs_collected = 0
    for job in Job.select().where(Job.status == 'READY'):
        jobs_submitted += await submit_job(job)
        jobs_polled += 1
    for job in Job.select().where(Job.status == 'RUNNING'):
        jobs_collected += await poll_active_job(job)
        jobs_polled += 1
    return jobs_polled, jobs_submitted, jobs_collected
