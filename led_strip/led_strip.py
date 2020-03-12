import time
import rpi_ws281x
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


# Class to  control the LED Strip based on the tweets.
class LedStripControl(threading.Thread):

    # Set up the strip with the passed parameters.  The Gamma correction is done by the library, so it gete passed in.
    def __init__(self, led_count, led_pin, led_freq_hz, led_dma, led_invert, led_brightness, led_msg_queue):

        super().__init__()

        self.led_count = led_count
        self.strip = rpi_ws281x.Adafruit_NeoPixel(led_count, led_pin, led_freq_hz, led_dma, led_invert,
                                                  led_brightness, gamma= gamma8)

        # Intialize the library (must be called once before other functions).
        self.strip.begin()
        self.led_msg_queue = led_msg_queue

    # Set the stip colours according to the state of the salt hopper.
    def set_strip_colours(self, remaining_salt_ratio):

        self.pixel_clear()

        # Figure out which pixel to light and which colour to use.
        pixel_to_light = int(float(remaining_salt_ratio) * self.led_count)

        minimum_pixels = 5

        if pixel_to_light < minimum_pixels:
            pixel_to_light = minimum_pixels

        print(pixel_to_light)

        if remaining_salt_ratio > 0.75:
            colour = rpi_ws281x.Color(0, 50, 0)
        elif .75 > remaining_salt_ratio > 0.20:
            colour = rpi_ws281x.Color(0, 0, 100)
        else:
            colour = rpi_ws281x.Color(255, 0, 0)

        # Scrolling down
        for pixel in range (0, pixel_to_light):
            #print(pixel)
            self.strip.setPixelColor(pixel, colour)
            self.strip.show()
            time.sleep(0.5)
            self.strip.setPixelColor(pixel, rpi_ws281x.Color(0, 0, 0))
            time.sleep(0.1)
            self.strip.show()

    # Clears al the pixels.
    def pixel_clear(self):
        # Clear all the pixels
        for i in range(0, self.strip.numPixels()):  # Green Red Blue
            self.strip.setPixelColor(i, rpi_ws281x.Color(0, 0, 0))

        self.strip.show()

    def run(self):

        remaining_salt_level = None

        while True:

            self.pixel_clear()
            time.sleep(5)
            while not self.led_msg_queue.empty(): # Clear out the queue as needed.
                remaining_salt_level = self.led_msg_queue.get_nowait()
                print(remaining_salt_level)

            if remaining_salt_level is not None:
                self.set_strip_colours(float(remaining_salt_level))


if __name__ == "__main__":

    print("main")

    # LED strip configuration:
    LED_COUNT      = 59      # Number of LED pixels.
    LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
    LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
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

