# BitMesh 📡

BitMesh is a mesh networking protocol implementation using Reticulum-based devices for long-range LoRa communication. It features automatic message fragmentation and reconstruction, allowing transmission of messages larger than the LoRa packet size limit.

## 🌟 Features

- 📦 Automatic message fragmentation and reconstruction
- ✅ Message integrity verification using MD5 checksums
- 📊 Real-time signal quality monitoring (RSSI & SNR)
- 🎨 Colorful terminal interface with status icons
- ⚙️ Configurable radio parameters
- 🔄 Automatic packet reassembly

## 🛠️ Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/bitmesh.git
   cd bitmesh
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## 📋 Requirements

- Python 3.7+
- RNode device
- Required Python packages:
  - colorama
  - rnode (RNode interface library)

## 🚀 Usage

Run BitMesh with default settings:
```
python main.py
```

### Command Line Options

- `--port`: Serial port for RNode (default: /dev/ttyUSB0)
- `--name`: Name for the RNode (default: My RNode)
- `--frequency`: Frequency in Hz (default: 868000000)
- `--bandwidth`: Bandwidth in Hz (default: 125000)
- `--txpower`: TX Power in dBm (default: 2)
- `--sf`: Spreading Factor (default: 7)
- `--cr`: Coding Rate (default: 5)

Example with custom settings:
```
python main.py --port /dev/ttyUSB1 --name "My RNode" --frequency 868100000 --bandwidth 125000 --txpower 10 --sf 7 --cr 5
```

## 📝 Message Format

Messages are automatically fragmented and include:
- Unique message ID
- Fragment number and total fragments
- MD5 checksum for integrity verification
- Message data
- Sender information

## 📊 Performance

The system provides real-time feedback on:
- Fragment transmission/reception status
- Signal strength (RSSI)
- Signal-to-noise ratio (SNR)
- Message reconstruction timing

## 🔧 Configuration

Default radio settings are optimized for:
- Maximum range while maintaining reasonable data rate
- Reliable message delivery
- Low power consumption

Adjust settings based on your specific needs using command line arguments.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

Please ensure compliance with local radio transmission regulations when using this software.

## 📞 Support

For issues and questions, please open an issue on the GitHub repository.
