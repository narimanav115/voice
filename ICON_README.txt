# ICON.ico - Placeholder

This file should be replaced with an actual .ico file for the application icon.

## Creating an icon:

### Option 1: Online converter
1. Create or find a 256x256 PNG image
2. Go to https://convertio.co/png-ico/
3. Convert PNG to ICO
4. Save as `icon.ico` in the project root

### Option 2: Using Python (PIL)
```python
from PIL import Image

# Load your image
img = Image.open('your_image.png')

# Resize to multiple sizes for better quality
img.save('icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
```

### Option 3: Use a default icon
For now, the build will work without an icon (it will use the default Python icon).

## Design suggestions for the icon:
- Use microphone + translation symbols
- Colors: Blue and green (representing audio/speech)
- Simple, recognizable at small sizes
- Include Russian/English flag elements

## Current status:
⚠️  No icon file present. Build will use default system icon.
To add: Create icon.ico and place it in the project root.
