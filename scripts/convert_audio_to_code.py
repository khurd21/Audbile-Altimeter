import argparse
import os
import wave
import struct
import sys

from dataclasses import dataclass

# INSTRUCTIONS:
# This is an automated script, ran by cmake, to help generate audio files for our device
# to read. It grabs all of the .wav files contained within the <AUDIO_FILE_DIRECTORY> (arg 1)
# and converts them to their respective .cpp files to be created inside <AUDIO_OUTPUT_DIRECTORY> (arg 2).

# The cmake will target the <AUDIO_OUTPUT_DIRECTORY> as an include directory, meaning you are able to
# include the generated files using #include "file.hpp". The majority of includes that use "" are most
# likely generated files.

_parser = argparse.ArgumentParser(description="Convert .wav files to .cpp files.")
_parser.add_argument("audio_file_directory", help="Path to the directory containing audio files")
_parser.add_argument("audio_output_directory", help="Path to the directory where output files will be saved")

_args = _parser.parse_args()

AUDIO_FILE_DIRECTORY = os.path.abspath(_args.audio_file_directory)
AUDIO_OUTPUT_DIRECTORY = os.path.abspath(_args.audio_output_directory)

AUDIO_SAMPLES_HEADER_FILE_NAME = 'audio_samples'
AUDIO_SAMPLE_ID_HEADER_FILE_NAME = 'sample_id'

AUDIO_SAMPLES_HEADER_FILE_PATH = AUDIO_OUTPUT_DIRECTORY
AUDIO_SAMPLE_ID_HEADER_FILE_PATH = AUDIO_OUTPUT_DIRECTORY

generated_warning = f'''
////////////////////////////////////////////////////////////////////////////////
///////////////////// THIS FILE IS AUTOGENERATED ///////////////////////////////
///////////////////// DO NOT EDIT !!!!!!        ////////////////////////////////
/// created by {os.path.basename(__file__)}
////////////////////////////////////////////////////////////////////////////////
'''

@dataclass
class SampleMetadata:
    full_path: str
    sample_name: str
    samples: list[int]
    num_samples: int

SAMPLE_RATE = 0
TOTAL_NUMBER_OF_BYTES = 0

def get_samples(wav_file):
    global SAMPLE_RATE
    samples = []
    with wave.open(wav_file, 'rb') as wav:
        assert wav.getsampwidth() == 2, "WAV file is not 16-bit"
        assert wav.getframerate() == 11025, "WAV file is not 11025 Hz"
        assert wav.getnchannels() == 1, "WAV file is not mono"
        SAMPLE_RATE = wav.getframerate()

        # Read frames and convert to 16-bit signed integers
        num_samples = wav.getnframes()
        frames = wav.readframes(num_samples)

        # Unpack the frames into a list of 16-bit signed integers
        samples = struct.unpack(f'<{num_samples}h', frames)
    return samples

def create_header_file_for_sample_id(samples: list[SampleMetadata]):
    header_file_path = os.path.abspath(os.path.join(AUDIO_SAMPLE_ID_HEADER_FILE_PATH, f'{AUDIO_SAMPLE_ID_HEADER_FILE_NAME}.hpp'))
    header_file_contents = generated_warning
    header_file_contents += f'''
#ifndef AUDIBLE_ALTIMETER_{AUDIO_SAMPLE_ID_HEADER_FILE_NAME.upper()}_H
#define AUDIBLE_ALTIMETER_{AUDIO_SAMPLE_ID_HEADER_FILE_NAME.upper()}_H

#include <cstdint>
#include <cstdio>

'''
    header_file_contents += f'inline constexpr std::size_t _TOTAL_NUMBER_OF_BYTES {{ {TOTAL_NUMBER_OF_BYTES} }};\n\n'
    header_file_contents += f"inline constexpr std::size_t SAMPLE_RATE {{ {SAMPLE_RATE} }};\n"
    header_file_contents += 'enum class AUDIO_SAMPLE_ID {\n'
    header_file_contents += '  BEGIN_SAMPLES = 0,\n'

    for i, sample in enumerate(samples):
        if i == 0:
            header_file_contents += f'  {sample.sample_name.upper()} = BEGIN_SAMPLES,\n'
        else:
            header_file_contents += f'  {sample.sample_name.upper()},\n'

    header_file_contents += f"  END_SAMPLES,\n"
    header_file_contents += f"  NUM_SAMPLES  = END_SAMPLES\n"
    header_file_contents += '};\n'
    header_file_contents += f'''
#endif // AUDIBLE_ALTIMETER_{AUDIO_SAMPLES_HEADER_FILE_NAME.upper()}_H
'''
    with open(header_file_path, 'w') as f:
        f.write(header_file_contents)  # Write each sample name on a new line

def create_header_file_for_samples(samples: list[SampleMetadata]):
    header_file_path = os.path.abspath(os.path.join(AUDIO_OUTPUT_DIRECTORY, f'{AUDIO_SAMPLES_HEADER_FILE_NAME}.hpp'))
    header_file_contents = generated_warning
    header_file_contents += f'''
#ifndef AUDIBLE_ALTIMETER_{AUDIO_SAMPLES_HEADER_FILE_NAME.upper()}_H
#define AUDIBLE_ALTIMETER_{AUDIO_SAMPLES_HEADER_FILE_NAME.upper()}_H

#include "{AUDIO_SAMPLE_ID_HEADER_FILE_NAME}.hpp"

#include <cstdint>
#include <array>\n
'''
    header_file_contents += '''
struct Audio_sample_location_and_size {
    std::int16_t* location;
    std::size_t size;
};\n
'''
    header_file_contents += f'inline constexpr std::size_t TOTAL_NUMBER_OF_BYTES {{ {TOTAL_NUMBER_OF_BYTES} }};\n'
    for sample in samples:
        header_file_contents += f'extern std::array<std::int16_t, {sample.num_samples}> {sample.sample_name};\n'

    header_file_contents += '''
using sample_lookup_t = std::array<Audio_sample_location_and_size,
                        static_cast<std::size_t>(AUDIO_SAMPLE_ID::NUM_SAMPLES)>;
inline constexpr sample_lookup_t sample_lookup = {
'''
    for sample in samples:
        header_file_contents += f'    Audio_sample_location_and_size{{ {sample.sample_name}.data(), {sample.sample_name}.size() }},\n'
    header_file_contents += "    };"

    header_file_contents += f'''
#endif // AUDIBLE_ALTIMETER_{AUDIO_SAMPLES_HEADER_FILE_NAME.upper()}_H
'''
    with open(header_file_path, 'w') as f:
        f.write(header_file_contents)  # Write each sample name on a new line


def create_cpp_files(samples: list[SampleMetadata]):
    # for sample in samples:


    for sample in samples:
        cpp_file_path = os.path.abspath(os.path.join(AUDIO_OUTPUT_DIRECTORY, f'{sample.sample_name}.cpp'))

        cpp_file_contents = generated_warning
        # Create the C++ array string
        cpp_file_contents += f'''#include "{AUDIO_SAMPLES_HEADER_FILE_NAME}.hpp"

#include <array>
#include <cstdint>\n
'''

        cpp_file_contents += f'std::array<std::int16_t, {sample.num_samples}> {sample.sample_name} = {{\n'
        cpp_file_contents += ',\n'.join(f'    {num}' for num in sample.samples)
        cpp_file_contents += '\n};'
        with open(cpp_file_path, 'w') as f:
            f.write(cpp_file_contents)  # Write each sample name on a new line

def collect_wav_samples_files(directory):
    sample_list: list[SampleMetadata] = []
    global TOTAL_NUMBER_OF_BYTES

    wav_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".wav"):
                wav_files.append(os.path.abspath(os.path.join(root, file)))

    for wav in wav_files:
        data = SampleMetadata(
            full_path=wav, sample_name=os.path.splitext(os.path.basename(wav))[0],
            samples=get_samples(wav), num_samples=len(get_samples(wav)))
        sample_list.append(data)
        TOTAL_NUMBER_OF_BYTES += (data.num_samples * 2)

    return sample_list


def main():
    samples = collect_wav_samples_files(AUDIO_FILE_DIRECTORY)
    create_header_file_for_samples(samples)
    create_header_file_for_sample_id(samples)
    create_cpp_files(samples)

if __name__ == '__main__':
    main()