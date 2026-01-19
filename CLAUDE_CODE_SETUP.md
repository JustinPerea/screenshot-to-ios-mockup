# Claude Code Setup Prompt

Copy and paste the prompt below into Claude Code to automatically set up the screenshot mockup generator.

---

## Setup Prompt

```
I want to use the screenshot mockup generator in this project. Please:

1. Install the Python dependencies by running: pip install -r requirements.txt

2. Verify the setup works by checking that the required modules can be imported

3. Show me how to create my first mockup

The main commands available are:
- python main.py screenshot <path-to-screenshot> - Create a single mockup
- python main.py batch <folder> - Process all screenshots in a folder
- python main.py platforms - List available platform presets

I have screenshots I want to turn into professional phone mockups for social media.
```

---

## Quick Start After Setup

Once dependencies are installed, here are common tasks:

### Create a mockup from a screenshot
```bash
python main.py screenshot path/to/screenshot.png
```

### Create mockups for all screenshots in a folder
```bash
python main.py batch my-screenshots/
```

### Use a specific platform preset
```bash
python main.py screenshot screenshot.png --platform instagram
```

### Use a specific background style
```bash
python main.py screenshot screenshot.png --background flowing
```

Available background styles: `expand`, `flowing`, `gradient`, `blobs`, `waves`, `aurora`

Available platforms: `twitter` (default), `instagram`, `square`, `story`, `wide`

---

## Example Claude Code Commands

Here are prompts you can use with Claude Code after setup:

- "Create a mockup from the screenshot at ~/Desktop/app-screenshot.png"
- "Process all PNG files in the screenshots folder and save mockups to output/"
- "Create an Instagram-optimized mockup with the aurora background style"
- "Show me the available platform presets and their dimensions"
