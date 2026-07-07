# Disk-Backed Job Metadata

Step PDF will store job metadata on disk as JSON instead of using a database. This preserves completed downloadable jobs across app restarts when files still exist, while accepting that queued or running jobs are marked failed after restart.
