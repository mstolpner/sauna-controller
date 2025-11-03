# Sauna Controller

![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)

A Raspberry Pi-based sauna controller with temperature monitoring, heating control, and web interface.

---

## ⚠️ CRITICAL SAFETY WARNING

**HIGH VOLTAGE SYSTEM - DANGER OF ELECTROCUTION AND FIRE**

This sauna controller interfaces with mains voltage electrical systems (120V/240V) and high-temperature heating elements. Improper installation, modification, or use can result in:

- ⚡ **Electric shock or electrocution**
- 🔥 **Fire hazard**
- 💀 **Death or serious injury**
- 🏠 **Property damage**

### MANDATORY REQUIREMENTS:

1. ✅ **Installation MUST be performed by a licensed electrician**
2. ✅ **Must comply with all local electrical codes and regulations**
3. ✅ **Must include appropriate safety cutoffs:**
   - Thermal fuses/cutoffs
   - Ground fault protection (GFCI/RCD)
   - Emergency stop switch
   - Over-temperature protection
4. ✅ **Regular safety inspections required**
5. ✅ **Never leave sauna unattended while heating**

**BY USING THIS PROJECT, YOU ACCEPT FULL RESPONSIBILITY AND ALL RISKS.**

---

## 📋 Features

- Temperature monitoring with multiple sensors
- Automatic heating control
- Web-based and local screen kivy-based user interface
- Safety limits and alerts
- Modbus RTU communication for industrial temperature controllers
- Raspberry Pi 5 compatible

---

## 🛠️ Hardware Requirements

- Raspberry Pi 5 (or compatible)
- Touch Display compatible with Raspberry Pi, similar to: https://www.amazon.com/dp/B0DP7BXFD3?ref=ppx_yo2ov_dt_b_fed_asin_title
- TTL to RS485 module compatible with 3V3 Raspberry Pi, for example https://www.aliexpress.us/item/3256809402393027.html?spm=a2g0o.order_list.order_list_main.61.7f2318029pp49C&gatewayAdapt=glo2usa
- RS485 Temperature sensors (https://store.comwintop.com/products/rs485-modbus-water-proof-temperature-humidity-sensor-probe or similar)
- JPF4816 Relay for light, fans, and low power heater control
- Contactor for Heater control
- Sauna heating elements
- Power supplies and proper electrical wiring
- You may need one or more DC-DC converters to power Raspberry Pi and Display. Note, that long power supply cables from power supplies may not work due to voltage drop and you may need to have a DC to DC converter close to the power consumer, like 24V -> 5V close to Raspberry Pi.
- Safety cutoffs and protection devices

## Hardware Diagram
![img_1.png](img_1.png)

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/mstolpner/sauna-controller.git
cd sauna-controller

# Install dependencies

# Configure your settings in sauna.ini file which will be created during first start

# Run the controller
python main.py
```

---

## 📜 License

This project is licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

### What this means:

#### ✅ You CAN (Non-Commercial Use):
- Build a controller for your personal home sauna
- Modify and improve the design
- Share your modifications with the community
- Use it for educational purposes or demonstrations
- Use in non-profit community projects or makerspaces
- Contribute improvements back to this project

#### ❌ You CANNOT (Commercial Use):
- Sell sauna controllers or components based on this design
- Offer sauna installation or maintenance services using this software
- Manufacture controllers or PCBs based on this design for sale
- Operate a commercial sauna facility using this controller
- Use in any service or product where customers pay money

### 🤝 Interested in Commercial Use?

If you'd like to use this project commercially, I'm open to discussing licensing options!  
Please contact me through GitHub: [@mstolpner](https://github.com/mstolpner)

### 📄 Full License

See the [LICENSE](LICENSE) file for complete terms.

[![License: CC BY-NC 4.0](https://licensebuttons.net/l/by-nc/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc/4.0/)

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### How to Contribute:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Note:** All contributions must be compatible with the CC BY-NC 4.0 license.

---

## ⚖️ Disclaimer

**NO WARRANTY:** This project is provided "AS IS" without warranty of any kind. The author assumes **NO LIABILITY** for any damages, injuries, or losses resulting from the use of this project.

**USE AT YOUR OWN RISK.** You are solely responsible for ensuring safe installation and operation.

---

## 🙏 Acknowledgments

- Thanks to the Raspberry Pi community
- Built with Python and modern web technologies
- Inspired by the love of a good sauna session 🧖

---

## 📞 Contact

- GitHub: [@mstolpner](https://github.com/mstolpner)
- Project Link: [https://github.com/mstolpner/sauna-controller](https://github.com/mstolpner/sauna-controller)

---

**Remember: Safety first. Always consult with professionals for electrical work. Enjoy your sauna responsibly! 🧖‍♂️🔥**
