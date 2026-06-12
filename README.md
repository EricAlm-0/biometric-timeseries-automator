# Biometric Time-Series Integrator: Garmin x Dexcom

An automated data pipeline designed to synchronize, clean, and consolidate high-resolution physiological data from **Garmin Connect** (smartwatch) and **Dexcom** (Continuous Glucose Monitor - CGM) into a single, unified time-series dataset. 

This project was developed independently to identify hidden correlations between physical activity, stress levels, heart rate, and glycemic responses.

---

## ⚙️ Key Features

- **Asynchronous Synchronization:** Resolves server-side sync delays by dynamically fetching rolling 24-hour windows from both APIs, ensuring zero gaps in data accumulation.
- **Time-Series Alignment:** Re-samples and merges heterogeneous data streams into synchronized, high-resolution 5-minute intervals using `pandas`.
- **Automated Execution:** Fully autonomous backend deployment utilizing Unix `cron` scheduling for daily maintenance-free updates.
- **Data Cleansing:** Implements logical validation gates to automatically filter out hardware error codes (e.g., negative anomaly filters in Garmin's stress metric values).

---

## 🛠️ Tech Stack & Architecture

- **Language:** Python 3
- **Data Engineering:** `pandas` (DataFrames, Outer Merges, Time-Rounding, GroupBy Aggregations), `numpy`
- **APIs & Protocols:** `garminconnect` wrapper, `pydexcom`
- **Automation:** Unix Crontab (macOS background daemon architecture)
- **Storage:** Normalized CSV (optimized for minimal storage footprints, ~5MB/year)

---

## 📊 Consolidated Data Schema

The pipeline merges the data streams into a structured relational CSV format using a synchronized UNIX-derived local timestamp:

| Column | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `timestamp` | String | `YYYY-MM-DD HH:MM` (Rounded to nearest 5 min) | Primary Key |
| `glukos` | Float | Blood glucose levels measured in mmol/L | Dexcom CGM |
| `stress` | Float | Stress score metrics calibrated from 0 to 100 | Garmin API |
| `steg` | Float | Aggregated step counts per 5-minute window | Garmin Sensor |
| `puls` | Float | Heart rate measured in beats per minute (BPM) | Garmin Optical Sensor |

*Note: Missing observations resulting from charging intervals or server sync delays are natively stored as `-` placeholders and automatically populated retroactively upon the next pipeline sweep.*

---

## 🚀 Getting Started & Installation

### 1. Clone the repository
```bash
git clone [https://github.com/your-username/garmin-dexcom-sync.git](https://github.com/your-username/garmin-dexcom-sync.git)
cd garmin-dexcom-sync
2. Install dependencies
Bash


pip install pandas garminconnect pydexcom
3. Configure credentials
Open kombinerad_halsa.py and input your secure API tokens/credentials within the dedicated environment block.
(Note: Never commit your actual passwords to GitHub. Keep the repository code clear of explicit credentials).

Python


# ─── CONFIGURATION BLOCK ─────────────────────────────
DEXCOM_USER     = "your_dexcom_username"
DEXCOM_PASS     = "your_dexcom_password"
DEXCOM_REGION   = "ous"  # 'ous' for Outside US, 'us' for US

GARMIN_EMAIL    = "your_garmin_email"
GARMIN_PASSWORD = "your_garmin_password"

OUTPUT_FILE     = "kombinerad_halsa.csv"
# ─────────────────────────────────────────────────────
4. Set up Automated Cron Scheduling
To configure the script to automatically wake up, extract, clean, and write the dataset every morning at 06:00 AM, initialize the Unix crontab daemon:

Bash


# Open crontab configuration using the nano text editor
EDITOR=nano crontab -e
Paste the following execution string (adjusting the directories to reflect your machine's absolute filepath environment):

Bash


0 6 * * * python3 "/absolute/path/to/Garmin x Dexcom/kombinerad_halsa.py"
Save and exit (Ctrl + O, Enter, Ctrl + X). The terminal should confirm: crontab: installing new crontab.

📈 Engineering Use Cases
This architecture serves as a robust foundation for downstream statistical analysis and data science deployments:

Time-Lag Analysis: Quantifying the exact physiological latency between high-intensity physical steps (steg) and subsequent metabolic glycemic drops (glukos).

Sleep Quality Evaluation: Correlating nocturnal autonomic nervous system metrics (Resting Heart Rate and Stress Scores) against fasting morning glucose baselines.

Correlation Matrices: Running predictive correlation sweeps using Python visualization libraries (matplotlib, seaborn) to uncover hidden systemic trends.

Developed as a personal engineering pipeline by a Mechanical Engineering Student at KTH Royal Institute of Technology.
