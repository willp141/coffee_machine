import machine # type: ignore
import os
import sdcard
import asyncio
from machine import Pin, I2S # type: ignore

class i2s_setup:
    def __init__(self) -> None:
        # Define the I2S pins
        self.bck_pin = Pin(26)   # BCLK (Bit Clock)
        self.ws_pin = Pin(25)    # LRC (Word Select or Left/Right Clock)
        self.sdout_pin = Pin(15) # DIN (Data in)

        # Create I2S object and initialize it
        self.audio_out = I2S(
            0,                       # I2S0 interface
            sck=self.bck_pin,         # BCLK pin
            ws=self.ws_pin,           # LRC pin
            sd=self.sdout_pin,        # Data output pin
            mode=I2S.TX,              # Transmit mode
            bits=16,                  # 16 bits per sample
            format=I2S.STEREO,        # Stereo format
            rate=44100,               # Sample rate (44.1 kHz)
            ibuf=8192                 # Buffer size
        )


class sdcard_setup:
    def __init__(self) -> None:
        self.cs = machine.Pin(16, machine.Pin.OUT)
        self.cs.value(1)  # Deselect SD card (CS high)

        # Initialize SPI bus for SD card with higher baud rate
        self.spi = machine.SPI(1, baudrate=20000000, polarity=0, phase=0, sck=machine.Pin(5), mosi=machine.Pin(18), miso=machine.Pin(19))

        # Initialize the SD card and mount the filesystem
        self.sd = sdcard.SDCard(self.spi, machine.Pin(16))  # CS pin connected to GPIO 16
        self.vfs = os.VfsFat(self.sd)
        os.mount(self.vfs, '/sd')
        print("SD Card mounted:", os.listdir("/sd"))
        self.audio_file_name = "/sd/sad.wav"


async def play_wav_async():
    """Asynchronously play a WAV file using asyncio"""
    sd = sdcard_setup()
    i2s = i2s_setup()

    try:
        # Open the WAV file in read-binary mode
        wav_file = open(sd.audio_file_name, 'rb')
        wav_file.seek(44)  # Skip the WAV header

        # Create asyncio StreamWriter for I2S output
        swriter = asyncio.StreamWriter(i2s.audio_out, {})

        # Define buffer size
        buffer_size = 8192
        audio_buffer = bytearray(buffer_size)

        while True:
            # Read from the WAV file asynchronously
            num_read = wav_file.readinto(audio_buffer)
            if num_read == 0:
                break  # End of file

            # Write data to I2S using asyncio
            swriter.write(audio_buffer[:num_read])
            await swriter.drain()  # Ensure the buffer is emptied

        print("Playback finished")

    except OSError as e:
        print(f"Error reading or writing file: {e}")

    finally:
        # Close the file and unmount the SD card
        if wav_file:
            wav_file.close()
        os.umount('/sd')