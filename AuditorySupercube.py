from typing import List

from tones.mixer import Mixer
from tones import SINE_WAVE
from playsound import playsound

from scipy import signal
from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt


class AuditorySupercube:

    def __init__(self):
        self.__mixer = None
        self.state_to_freq = {}
        self.freq_to_state = {}
        file = open("absolute_positioning.txt")
        lines = file.readlines()
        for line in lines:
            parts = line.split(" ")
            self.state_to_freq[parts[0]] = float(parts[1])
            self.freq_to_state[float(parts[1])] = parts[0]

        self.state = {'U': 0, "D": 0, "F": 0, "B": 0, "R": 0, "L": 0}
        for k, v in self.state_to_freq.items():  # Included to double check proper reading of the file.
            print("%s %s" % (k, v))

    def __str__(self):
        return ' U' + str(self.state['U']) + \
               ' D' + str(self.state['D']) + \
               ' F' + str(self.state['F']) + \
               ' B' + str(self.state['B']) + \
               ' R' + str(self.state['R']) + \
               ' L' + str(self.state['L'])

    def U(self):
        self.state['U'] = (self.state['U'] + 1) % 4

    def D(self):
        self.state['D'] = (self.state['D'] + 1) % 4

    def F(self):
        self.state['F'] = (self.state['F'] + 1) % 4

    def B(self):
        self.state['B'] = (self.state['B'] + 1) % 4

    def R(self):
        self.state['R'] = (self.state['R'] + 1) % 4

    def L(self):
        self.state['L'] = (self.state['L'] + 1) % 4

    def Uprime(self):
        self.state['U'] = (self.state['U'] + 3) % 4

    def Dprime(self):
        self.state['D'] = (self.state['D'] + 3) % 4

    def Fprime(self):
        self.state['F'] = (self.state['F'] + 3) % 4

    def Bprime(self):
        self.state['B'] = (self.state['B'] + 3) % 4

    def Rprime(self):
        self.state['R'] = (self.state['R'] + 3) % 4

    def Lprime(self):
        self.state['L'] = (self.state['L'] + 3) % 4

    def apply_alg(self, alg: str, tps: float, simulation: bool = False):
        moves = alg.split(" ")
        if simulation:  # Represent the initial cube state
            if not self.__mixer:
                self.__create_mixer()
            self.__append_state_to_mixer(tps=tps)
            self.__append_state_to_mixer(tps=tps)
            self.__append_state_to_mixer(tps=tps)
            self.__append_state_to_mixer(tps=tps)
            self.__append_state_to_mixer(tps=tps)
        for move in moves:
            if move == "U":
                self.U()
            if move == "D":
                self.D()
            if move == "F":
                self.F()
            if move == "B":
                self.B()
            if move == "R":
                self.R()
            if move == "L":
                self.L()
            if move == "U'":
                self.Uprime()
            if move == "D'":
                self.Dprime()
            if move == "F'":
                self.Fprime()
            if move == "B'":
                self.Bprime()
            if move == "R'":
                self.Rprime()
            if move == "L'":
                self.Lprime()
            if simulation:
                self.__append_state_to_mixer(tps=tps)
            print(self)

    def play_simulation(self, silent: bool = False):
        # Mix all tracks into a single list of samples and write to .wav file
        if self.__mixer:
            self.__mixer.write_wav('tones.wav')
            if not silent:
                playsound('tones.wav')
        else:
            print("ERROR: No simulation to play")

    def __create_mixer(self):
        self.__mixer = Mixer(44100, 1)
        self.__mixer.create_track('U', SINE_WAVE, attack=0.01, decay=0.1)
        self.__mixer.create_track('D', SINE_WAVE, attack=0.01, decay=0.1)
        self.__mixer.create_track('F', SINE_WAVE, attack=0.01, decay=0.1)
        self.__mixer.create_track('B', SINE_WAVE, attack=0.01, decay=0.1)
        self.__mixer.create_track('R', SINE_WAVE, attack=0.01, decay=0.1)
        self.__mixer.create_track('L', SINE_WAVE, attack=0.01, decay=0.1)

    def __append_state_to_mixer(self, tps: float):
        self.__mixer.add_tone('U', self.state_to_freq['U' + str(self.state['U'])], 1 / tps)
        self.__mixer.add_tone('D', self.state_to_freq['D' + str(self.state['D'])], 1 / tps)
        self.__mixer.add_tone('F', self.state_to_freq['F' + str(self.state['F'])], 1 / tps)
        self.__mixer.add_tone('B', self.state_to_freq['B' + str(self.state['B'])], 1 / tps)
        self.__mixer.add_tone('R', self.state_to_freq['R' + str(self.state['R'])], 1 / tps)
        self.__mixer.add_tone('L', self.state_to_freq['L' + str(self.state['L'])], 1 / tps)

    def extract_alg_from_audio(self, wav_path):
        state_over_time = self.__extract_state_over_time(wav_path)
        alg = self.extract_alg_from_state_over_time(state_over_time)
        return alg

    def __extract_state_over_time(self, wav_path):
        SAMPLES_PER_WINDOW = 1024  # Seems to be a good number to balance frequency precision with time precision.
        # THRESHOLD = 1500  # The minimum value required for a frequency to be detected as present.
        sample_rate, audio_samples = wavfile.read(wav_path)
        freq, time, Zxx = signal.stft(audio_samples,
                                      fs=sample_rate,
                                      nperseg=SAMPLES_PER_WINDOW,
                                      noverlap=(SAMPLES_PER_WINDOW // 4) * 3)
        # Determine the frequencies of interest
        spectrogram = np.abs(Zxx).transpose()
        # Show off a spectrogram of the detected audio
        # plt.pcolormesh(time, freq, np.abs(Zxx), shading='gouraud')
        # plt.title('STFT Magnitude')
        # plt.ylabel('Frequency [Hz]')
        # plt.xlabel('Time [sec]')
        # plt.show()
        state_over_time = []
        for time_idx in range(len(time)):
            important_freqs = []
            threshold = np.std(spectrogram[time_idx])
            plt.plot(freq, spectrogram[time_idx])
            plt.axhline(threshold, color='red')
            plt.axis([0, 20000, 0, 4000])
            plt.title(f"Frequencies at {time[time_idx]:.2f} seconds")
            plt.ylabel("Strength")
            plt.xlabel("Frequency [Hz]")
            plt.savefig(f"./plt/{time[time_idx]:.2f}.png")
            plt.clf()
            for freq_idx in range(len(freq)):
                if spectrogram[time_idx][freq_idx] > threshold:
                    important_freqs.append((freq[freq_idx], spectrogram[time_idx][freq_idx]))
            if len(important_freqs) > 0:
                detected_states = self.get_state_from_freq(important_freqs)
                state_over_time.append((time[time_idx], detected_states))
                print(f"At time {time[time_idx]:.6f} the states {detected_states} were detected based on the "
                      f"{len(important_freqs)} frequencies {important_freqs} that surpassed the threshold.")
        return state_over_time

    def get_state_from_freq(self, detected_freqs: List[float]) -> List[str]:
        detected_states = {}
        strongest_state = {
            "U": 0,
            "D": 0,
            "R": 0,
            "L": 0,
            "F": 0,
            "B": 0,
        }
        for d_freq, power in detected_freqs:
            for s_freq in self.freq_to_state.keys():
                if abs(d_freq - s_freq) < 40:
                    state = self.freq_to_state[s_freq]
                    face = state[0]
                    rotation = int(state[1])
                    if power > strongest_state[face]:
                        detected_states[face] = rotation
                        strongest_state[face] = power
        return detected_states

    def extract_alg_from_state_over_time(self, state_over_time):
        useful_states = [x for x in state_over_time if len(x[1]) == 6 and 'ERR' not in x[1]]
        current_state = useful_states[0][1]
        alg = ""
        for state in useful_states[1:]:
            """temp string for pausing"""
            for face in ["U", "D", "F", "B", "R", "L"]:
                rotation = state[1][face] - current_state[face]
                if rotation != 0:
                    current_state[face] = state[1][face]
                    if rotation == 1:  # Next state up
                        alg += " " + face
                    elif rotation == -1:  # Next state down
                        alg += " " + face + "'"
                    elif rotation == -3:  # Next state up with wrap-around
                        alg += " " + face
                    elif rotation == 3:  # Next state down with wrap-around
                        alg += " " + face + "'"
        return alg


a_cube = AuditorySupercube()

given_alg = "U U U U D D D D R R R R L L L L F F F F B B B B"
given_tps = 5
a_cube.apply_alg(given_alg, given_tps, simulation=True)
a_cube.play_simulation(silent=True)
received_alg = a_cube.extract_alg_from_audio("./output.wav")

print(f"Given Alg: {given_alg}\nReceived Alg: {received_alg}")
print("MATCH!" if given_alg.strip() == received_alg.strip() else "MISMATCH :(")

# pos = AuditorySupercube()
# pos.transmitAlg("U U U U D D D D R R R R L L L L F F F F B B B B", 1.5)
# pos.playSound()
# pos.parseAlg("U U U U", 2)
# pos.playSound()
# pos.parseAlg("D D D D", 2)
# pos.playSound()
# pos.parseAlg("R R R R", 2)
# pos.playSound()
# pos.parseAlg("L L L L", 2)
# pos.playSound()
# pos.parseAlg("F F F F", 2)
# pos.playSound()
# pos.parseAlg("B B B B", 2)
# pos.playSound()
