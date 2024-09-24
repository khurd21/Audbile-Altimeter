#ifndef AUDIBLE_ALTIMETER_AUDIO_PLAYER_HPP
#define AUDIBLE_ALTIMETER_AUDIO_PLAYER_HPP
#include <Audible-Altimeter/audio_driver.hpp>
#include <Audible-Altimeter/sample_id.hpp>
#include <cstdint>

constexpr int RAND_INT_IN_AUDIO_PLAYER_H{5};

class AudioPlayer {
 public:
  AudioPlayer(AudioDriver& impl);

  bool play(AUDIO_SAMPLE_ID sample_id);

  void set_volume_on_all_samples(std::int16_t new_volume);

 private:
  AudioDriver& m_impl;
};
#endif  // AUDIBLE_ALTIMETER_AUDIO_PLAYER_HPP
// Unable to find executable file at /Users/si/code/pico/vscode_picoexamples/Audbile-Altimeter/build/Audible-Altimeter.elf