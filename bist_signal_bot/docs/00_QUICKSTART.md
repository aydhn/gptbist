# Quickstart

BIST Signal Bot local deployment and quick usage instructions (10-minute setup).

1. **Clone the repository and prepare environment**
   `git clone <repo-url>`
   `cd bist_signal_bot`
   `python -m venv venv`
   `source venv/bin/activate`

2. **Install Packages**
   `pip install -r requirements.txt`

3. **Check Environment**
   `python -m bist_signal_bot deploy doctor`

4. **Initialize Config and First Run (Dry Run)**
   `python -m bist_signal_bot deploy first-run --dry-run`

5. **Run Healthcheck**
   `python -m bist_signal_bot healthcheck`

6. **Check Scheduler Due Jobs (Dry Run)**
   `python -m bist_signal_bot scheduler run-due --dry-run`

7. **Release Readiness Check**
   `python -m bist_signal_bot release readiness`
