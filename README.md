# Teleprompter

A desktop teleprompter application built with Python and PySide6. It allows you to display and auto-scroll a text file in sync with an audio track, making it ideal for presentations, speeches, or music performances.

## Features

- Select a text file to display as a script or lyrics.
- Select an audio file (MP3, WAV, M4A, MP4, WV) to play alongside the text.
- Adjustable font size for better readability.
- Configurable scroll duration and start delay.
- Pause, resume, and stop controls for both audio and scrolling.
- Fullscreen mode for distraction-free reading.
- Visual countdown before scrolling starts.

## Requirements

- Python 3.7+
- PySide6
- pygame
- mutagen

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Click "Seleccionar archivo de texto" to choose your script or lyrics file.
3. Click "Seleccionar instrumental" to choose your audio file.
4. Set the desired delay and manual duration (in MM:SS or seconds).
5. Click "Iniciar" to start the teleprompter.
6. Use the on-screen controls to play, pause, stop, or adjust font size.

## Notes

- The scroll speed is automatically calculated based on the duration you set.
- You can adjust the font size at any time using the + and - buttons.
- The application supports most common audio formats via the `mutagen` library.

## License

MIT License
