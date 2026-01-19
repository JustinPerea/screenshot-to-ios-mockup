# Device Frame Assets

This folder contains device frame PNG images used for mockups.

## Adding Custom Frames

To use a real iPhone frame PNG instead of the procedural one:

1. Download a transparent PNG mockup frame from one of these sources:
   - [WebMobileFirst](https://www.webmobilefirst.com/en/mockups/) - Free HD PNG mockups
   - [Freepik](https://www.freepik.com/free-photos-vectors/iphone-mockup-transparent) - Various iPhone mockups
   - [Vecteezy](https://www.vecteezy.com/free-png/iphone-mockup) - 450+ iPhone mockup PNGs

2. Name the file according to the device:
   - `iphone_15_pro_max.png`
   - `iphone_16_pro_max.png`
   - `iphone_17_pro_max.png`

3. Update screen coordinates in `src/mockup/device_frame.py`:
   ```python
   IPHONE_15_PRO_MAX = DeviceSpec(
       name="iPhone 15 Pro Max",
       frame_path="iphone_15_pro_max.png",
       screen_size=(862, 1868),  # Width, Height of screen area
       screen_offset=(38, 29),   # X, Y from top-left to screen
       corner_radius=100,
       frame_color=(30, 30, 35, 255)
   )
   ```

## Measuring Screen Coordinates

To find the correct `screen_size` and `screen_offset` for a new frame:

1. Open the frame PNG in an image editor
2. Measure the screen area dimensions (the black/transparent area for the display)
3. Measure the offset from the top-left corner of the image to the top-left of the screen
4. Update the `DeviceSpec` accordingly

## Current Frames

| Device | File | Status |
|--------|------|--------|
| iPhone 15 Pro Max | `iphone_15_pro_max.png` | Not included (add manually) |
| iPhone 16 Pro Max | `iphone_16_pro_max.png` | Not included (add manually) |
| iPhone 17 Pro Max | `iphone_17_pro_max.png` | Uses procedural fallback |

## Procedural Fallback

If no PNG frame is found, the system generates a procedural frame with:
- Realistic titanium-style bezels
- Side buttons (Action Button, Volume Up/Down)
- Dynamic Island
- Edge highlights for metallic look
- Proper rounded corners

The procedural frame looks good for most uses, but real PNG frames provide more photorealistic results.
