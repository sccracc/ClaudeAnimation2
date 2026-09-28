"""Generate the narration take with OpenRouter TTS (gpt-audio, voice 'ash'). ~$0.07 per full take."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orclient, script

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(orclient.ROOT, 'assets', 'audio', 'narration_take1.wav')
    print(orclient.tts("\n".join(script.LINES), out, instructions=script.INSTRUCTIONS, purpose='narration take', est=0.15, **script.VOICE))
