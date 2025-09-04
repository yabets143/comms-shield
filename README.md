# 🛡️ Defensive Communication Security Toolkit  
**Defending Against Metadata Leaks & Covert Channels**

---

## 📖 Overview
This project provides a **two-layer defensive system** to protect communication channels from common espionage threats:  

1. **Metadata Leak Prevention System (MLPS)**  
   - Scrubs sensitive metadata from files, emails, and documents before transmission.  
   - Prevents adversaries from extracting operational security (OPSEC) details such as device info, geolocation, software versions, and communication patterns.  

2. **Defensive Steganography Scanner (DSS)**  
   - Detects hidden data embedded in images, audio, and documents (steganography).  
   - Protects against covert exfiltration techniques often used in cyber-espionage.  

Together, these tools provide a **defensive shield for secure communications** against adversarial intelligence collection.  



## 🎯 Objectives
- Prevent **metadata-based intelligence gathering**.  
- Detect and mitigate **covert communication channels**.  
- Provide a **dashboard for operators** to monitor communication artifacts and ensure they are sanitized before release.  
- Demonstrate **practical defensive measures** in the field of communication cybersecurity.  

## ⚙️ Features
✅ Strip EXIF metadata from images (JPEG, PNG).  
✅ Remove metadata from PDFs & DOCX files.  
✅ Sanitize email headers before sending.  
✅ Detect LSB-based image steganography.  
✅ Detect anomalies in audio frequency patterns.  
✅ Identify suspicious spacing/encoding in PDFs.  
✅ Dashboard with logs, alerts, and reports.  

---
# Arcitechture 

                   ┌───────────────────────────┐
                   │  User Communication Input  │
                   │ (Email, File, Media, Chat) │
                   └───────────────┬───────────┘
                                   │
                ┌──────────────────┴───────────────────┐
                │                                      │
      ┌─────────▼─────────┐                  ┌─────────▼─────────┐
      │ Metadata Scrubber │                  │ Steganography Scan │
      │ (strip EXIF,      │                  │ (LSB, audio, text) │
      │ headers, doc info)│                  └─────────┬─────────┘
      └─────────┬─────────┘                            │
                │                                      │
                └──────────────────┬───────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   Logging & Report  │
                        │   (SQLite/Postgres) │
                        └──────────┬──────────┘
                                   │
                          ┌────────▼────────┐
                          │   Dashboard     │
                          │ (Flask/FastAPI) │
                          └─────────────────┘
