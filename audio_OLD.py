from machine import Pin, I2S # type: ignore
import os

# Setup I2S
def setup_i2s():
    # Define I2S pins for ESP32
    bck_pin = Pin(26)  # Bit Clock (BCK)
    ws_pin = Pin(25)   # Word Select (LRC)
    sdout_pin = Pin(22)  # Serial Data Output (DIN)

    audio_out = I2S(
        0,                   # I2S interface ID (I2S0)
        sck=bck_pin,          # BCK pin
        ws=ws_pin,            # LRC pin
        sd=sdout_pin,         # Data output (DIN)
        mode=I2S.TX,          # Transmit mode (TX)
        bits=16,              # 16 bits per sample
        format=I2S.STEREO,    # Stereo output
        rate=44100,           # 44.1 kHz sample rate
        ibuf=8192             # Buffer size
    )
    
    return audio_out

# Function to play WAV file from internal storage
def play_wav_file():
    audio_out = setup_i2s()

    # Assuming you uploaded the 'sample.wav' to the board's internal filesystem
    wav_file = open("/sad.wav", "rb")
    wav_file.seek(44)  # Skip the WAV header

    buffer_size = 8192  # Adjust the buffer size as needed
    audio_buffer = bytearray(buffer_size)

    while True:
        num_read = wav_file.readinto(audio_buffer)
        if num_read == 0:
            break  # End of file

        # Write buffer to I2S
        audio_out.write(audio_buffer[:num_read])

    wav_file.close()
    print("Playback finished")

