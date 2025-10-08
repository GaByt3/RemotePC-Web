# 🚀 Web Remote Control (RemotePC Web Interface)

[![Python](https://img.shields.io/badge/python-3.10+-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A **web-based computer remote control system** that allows you to view the screen, send commands, type text, use key combinations, and control the mouse in real-time. Supports multiple monitors and is accessible from any authorized device.

> ⚠️ Currently, the project works only on **local networks**. Future updates will enable access and control from anywhere.  
> ⚠️ Use within a trusted network. Do not expose publicly without proper security measures.

---

## 🌟 Features

- Real-time PC screen viewing
- Send commands and type text (virtual keyboard & CMD)
- Advanced controls: special keys, key combinations, and mouse
- Multi-monitor support
- Responsive interface for desktop, tablet, and mobile
- Secure connection via one-time QR code and session control by IP

---

## 📸 Screenshots

<img width="1919" height="1031" alt="RemotePC Web Screenshot 1" src="https://github.com/user-attachments/assets/753c35d4-a6fe-44ff-a95e-6facf4cedc0f" />
<img width="1917" height="1031" alt="RemotePC Web Screenshot 2" src="https://github.com/user-attachments/assets/64f8fc3f-61df-46d8-8987-fc69508fc1ee" />

---

## ⚡ How It Works

1. Run the server locally.  
2. Open a web browser on the device you want to use for control.  
3. Scan or click the QR code to authorize the device.  
4. Enjoy full control of your PC in real-time.

---

## 🛠 Installation

```bash
git clone https://github.com/GaByt3/remotepc-web.git
cd remotepc-web
pip install -r requirements.txt
python app.py
```

## 🔒 Security

* Each session is restricted to a single authorized IP.
* One-time use token via QR code.
* Prevents unauthorized simultaneous access even if someone has the token.

## 🚀 Future Plans

* Remote access via the internet (outside local network)
* Improved interface and responsiveness
* Support for multiple simultaneous sessions (with security)
* Enhanced mobile and multi-monitor UI


