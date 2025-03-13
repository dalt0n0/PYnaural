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