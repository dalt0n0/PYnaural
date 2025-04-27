# PYnaural - Binaural Beat Generator

A powerful and user-friendly binaural beat generator with support for multiple track types and advanced audio features.

## Features

- **Multiple Track Types**:
  - Binaural Beats
  - White/Pink/Brown Noise
  - Pure Tones
  
- **Advanced Audio Controls**:
  - Frequency Modulation
  - Isochronic Pulses
  - Stereo Panning
  - Volume Control
  
- **Export Capabilities**:
  - Save as WAV files
  - Export/Import settings as JSON

## Installation & Running

### Windows Users
1. Make sure you have Python 3.11 or later installed
2. Download or clone this repository
3. Double-click `launch.bat` - it will:
   - Create a virtual environment if needed
   - Install required dependencies
   - Launch the application

### Manual Installation
If you prefer to set things up manually:
1. Clone this repository
2. Create a virtual environment: `python -m venv env`
3. Activate the environment:
   - Windows: `env\Scripts\activate`
   - Unix/MacOS: `source env/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python binaural_app.py`

## Usage

1. **Adding Tracks**:
   - Click the "➕" buttons to add different types of tracks
   - Each track can be individually configured

2. **Track Types**:
   - **Binaural Beat**: Set base frequency and beat frequency
   - **Noise**: Choose noise type and frequency range
   - **Tone**: Set frequency with optional modulation and pulses

3. **Controls**:
   - Use sliders to adjust frequencies and volumes
   - Enable/disable tracks using checkboxes
   - Set master volume and duration

4. **Panning Options**:
   - Center
   - Hard-left/right
   - Auto-pan with customizable speed and depth

5. **Exporting**:
   - Click "Export to WAV" to save your audio
   - Use "Export Settings" to save your configuration

## Requirements
- Python 3.11+
- numpy
- sounddevice
- soundfile
- scipy
- pygame
- pillow (for icon creation)

## Development
- The project uses a virtual environment for dependency management
- `launch.bat` handles environment setup and running the application
- Use `requirements.txt` for managing Python dependencies

## License
MIT License - Feel free to use and modify as needed.

## Contributing
Contributions are welcome! Please feel free to submit pull requests.

## Audio Generation Details

### Noise Generation
The application supports three types of noise:
- **White Noise**: Pure random noise with equal energy across all frequencies
- **Pink Noise**: Noise with equal energy per octave (1/f), created using a moving average filter
- **Brown Noise**: Noise with energy decreasing by 6dB per octave (1/f²), created using a larger moving average filter

### Frequency Control
- **Low Cut**: Applies a high-pass filter to remove frequencies below the specified value
- **High Cut**: Applies a low-pass filter to remove frequencies above the specified value
- Both filters use 4th-order Butterworth filters for clean frequency response

### Panning
The application supports several panning modes:
- **Left**: Audio plays only in the left channel
- **Right**: Audio plays only in the right channel
- **Center**: Audio plays equally in both channels
- **L-R**: Smooth panning sweep from left to right
- **R-L**: Smooth panning sweep from right to left

Panning controls:
- **Speed**: Controls how fast the panning sweeps occur (in Hz)
- **Depth**: Controls how extreme the panning is (0 = centered, 1 = full pan)

### Audio Processing
- Sample rate: 44.1kHz
- Block size: 1024 samples
- Soft clipping is applied to prevent digital distortion
- Gain compensation ensures consistent volume levels across different noise types
- Thread-safe audio generation to prevent glitches

### Technical Notes
- The application uses `sounddevice` for real-time audio playback
- `numpy` is used for efficient audio processing
- `scipy.signal` provides the filtering functions
- All audio processing is done in real-time with minimal latency
- The application includes proper error handling and resource cleanup 