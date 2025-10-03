# 🛡️ Defensive Communication Security Toolkit  
**Defending Against Metadata Leaks & Covert Channels**

---

## 📖 Overview

This project provides a Metadata Leak Prevention System (MLPS) to protect communication channels and file workflows from espionage threats:

- Scrubs sensitive metadata from files, emails, and documents before transmission.

- Monitors a selected folder in real time and automatically scrubs any files placed inside.

- Prevents adversaries from extracting operational security (OPSEC) details such as device info, geolocation, software versions, and communication patterns.

Together, these capabilities provide a defensive shield for secure communications against adversarial intelligence collection.



## Prevent metadata-based intelligence gathering.

- Automate file sanitization by monitoring sensitive folders.

- Provide a dashboard for operators to monitor communication artifacts and ensure they are sanitized before release.

- Demonstrate practical defensive measures in the field of communication cybersecurity.

## ⚙️ Features

✅ Folder Watcher – continuously monitors a user-selected folder and scrubs all files dropped in.

✅ Strip EXIF metadata from images (JPEG, PNG).

✅ Remove metadata from PDFs & DOCX files.

✅ Sanitize email headers before sending.

✅ Dashboard with logs, alerts, and reports.

### future extensions
✅ Detect LSB-based image steganography.  
✅ Detect anomalies in audio frequency patterns.  
✅ Identify suspicious spacing/encoding in PDFs.  

---
# Usage 

## installation 

clone the repo
```
git clone <repo-link>
cd comms-shield
```
create virtual enviroments (recommended)

```
python -m venv env


#for windows
.\env\Scripts\activate

# for linux
source env/bin/activate 
```


install dependecies 

```
pip install -r requirments.txt
```

## to run the UI 

```
python proxy.py
```

## to use the universal scrubber on terminal 

```
python universal_scrubber.py <your-file>
```
