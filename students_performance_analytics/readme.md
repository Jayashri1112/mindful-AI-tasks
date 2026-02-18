# 🎓 Academic Performance Tracker

A professional web-based system designed for academic departments to track internal assessments, analyze student performance, and identify at-risk students requiring intervention.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🚀 Features

- **📊 Interactive Dashboard:** Visualize overall performance, subject averages, and mark distributions.
- **📝 Secure Data Entry:** Manually enter student details and assessment marks with validation.
- **⚠️ At-Risk Identification:** Automatically flags students with average marks below a specific threshold (default 50%).
- **📥 Data Export:** Download performance reports and intervention lists in CSV format.
- **💾 Persistent Storage:** Uses SQLite to ensure data is saved securely between sessions.

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Data Analysis:** Pandas
- **Visualization:** Plotly
- **Database:** SQLite3

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python Package Installer)

## ⚙️ Installation

1. **Clone the repository or download the files:**
   Ensure you have `app.py`, `requirements.txt`, and `README.md` in the same directory.

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv venv