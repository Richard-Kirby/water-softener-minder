import time
import rpi_ws281x
import colorsys
import threading
import queue

# Gamma correction makes the colours perceived correctly.
gamma8 = [
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,
    1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,
    2,  3,  3,  3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  5,  5,  5,
    5,  6,  6,  6,  6,  7,  7,  7,  7,  8,  8,  8,  9,  9,  9, 10,
   10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
   17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
   25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
   37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
   51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
   69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
   90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
  115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
  144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
  177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
  215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255]


# Class to control the LED Strip based on the height of the salt.
class LedStripControl(threading.Thread):

    # Set up the strip with the passed parameters.  The Gamma correction is done by the library, so it gete passed in.
    # The gamma correction ensures the colour is adequately represented.
    def __init__(self, led_count, led_pin, led_freq_hz, led_dma, led_invert, led_brightness, led_msg_queue):

        super().__init__()

        self.led_count = led_count

        # Neopixel strip initialisation.
        self.strip = rpi_ws281x.Adafruit_NeoPixel(led_count, led_pin, led_freq_hz, led_dma, led_invert,
                                                  led_brightness, gamma= gamma8)

        # Initialise the library (must be called once before other functions).
        self.strip.begin()
        self.led_msg_queue = led_msg_queue

        # create the colours to be used for the bar graph, spread evenly over hte total pixels
        low_colour = 0
        full_colour = 0.4

        colour_step = float((full_colour - low_colour) / self.led_count)

        hue = full_colour  # start the hue at full as we count down.
        self.rgb_colour_list = []

        # Create the colour mapping to use.  Red at the bottom (empty), green at the top (full).
        for colour in range(0, self.led_count):
            hue = hue - colour_step
            if hue < low_colour:
                hue = low_colour

            rgb_colour = colorsys.hsv_to_rgb(hue, 1, 0.5)
            rgb_colour = [int(element * 255) for element in rgb_colour]
            #print(hue, rgb_colour)
            self.rgb_colour_list.append(rpi_ws281x.Color(*tuple(rgb_colour)))

    # Set the stip colours according to the state of the salt hopper.
    def set_strip_colours(self, remaining_salt_ratio):

        # Start from a clear slate.
        self.pixel_clear()

        # Figure out which pixel to light and which colour to use.
        pixel_to_light = round(float(self.led_count - float(remaining_salt_ratio * self.led_count))) - 1

        # Limiting the pixels to the available ones.  Don't go below -1 when counting down.
        if pixel_to_light < -1:
            pixel_to_light = -1

        minimum_pixels = self.led_count - 5 # Need at least 5 pixels to get a decent visual. Count from bottom of strip.

        # This is to ensure we get the minimum # of pixels otherwise hard to see or know the program is working.
        if pixel_to_light > minimum_pixels:
            pixel_to_light = minimum_pixels

        #print("go to {}, ratio {}" .format(pixel_to_light, remaining_salt_ratio))

        # Scrolling down
        for pixel in range(self.led_count-1, pixel_to_light, -1):
            self.strip.setPixelColor(pixel, rpi_ws281x.Color(0, 0, 0))
            time.sleep(0.5)
            self.strip.show()

            # Pixel colour set according to the scheme defined in __init__
            self.strip.setPixelColor(pixel, self.rgb_colour_list[pixel])
            time.sleep(0.5)
            self.strip.show()

    # Clears al the pixels.
    def pixel_clear(self):
        # Clear all the pixels
        for i in range(0, self.strip.numPixels()):  # Green Red Blue
            self.strip.setPixelColor(i, rpi_ws281x.Color(0, 0, 0))

        self.strip.show()

    # The run function is what gets called when the thread is started.
    def run(self):

        remaining_salt_level = None

        while True:

            while not self.led_msg_queue.empty(): # Clear out the queue as needed.  This is in case it gets behind.
                remaining_salt_level = self.led_msg_queue.get_nowait()
                #print(remaining_salt_level)

            if remaining_salt_level is not None:
                self.set_strip_colours(float(remaining_salt_level))

            time.sleep(30)


if __name__ == "__main__":

    print("main")

    # LED strip configuration:
    LED_COUNT      = 59      # Number of LED pixels.
    LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
    LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA        = 10       # DMA channel to use for generating signal (try 5)
    LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
    LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

    remaining_salt_ratio_queue = queue.Queue()

    water_strip = LedStripControl(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS,
                                  remaining_salt_ratio_queue)

    water_strip.start()

    try:

        while True:

            print("loop")
            for i in range(1, 10):
                remaining_salt_ratio_queue.put_nowait(float(i/10))
                print(i/10)
                time.sleep(10)

    except:
        raise

    finally:
        water_strip.pixel_clear()

