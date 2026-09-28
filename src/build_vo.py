"""Cut the single narration take into lines, re-space them on the film timeline, export timing cues."""
import json, wave, numpy as np
from scipy.signal import resample_poly, butter, sosfilt
import vo_analyze, script

SR = 48000
LEAD = 1.0                      # narration starts 1s into the film
EXTRA = {5: 0.4, 8: 0.6}        # extra breathing room before line index (0-based): dream reveal, morning

def build(take='assets/audio/narration_take1.wav'):
    x, sr = vo_analyze.load(take)
    segs = vo_analyze.segments(x, sr, min_gap=0.3)
    # group phrase segments into lines using the long pauses between sentences (script has 9 lines)
    gaps = [(segs[i + 1][0] - segs[i][1], i) for i in range(len(segs) - 1)]
    # sentence boundaries = the (n_lines-1) phrase gaps that sit after sentence-final punctuation.
    # We identify them by known phrase counts per line (derived from punctuation in the script).
    counts = [4, 3, 1, 3, 4, 2, 3, 3, 2]
    assert sum(counts) == len(segs), (len(segs), segs)
    lines = []; k = 0
    for n in counts:
        lines.append(segs[k:k + n]); k += n
    out = np.zeros(int(SR * 62))
    cues = {'lines': []}
    shift = LEAD
    for i, ph in enumerate(lines):
        shift += EXTRA.get(i, 0.0)
        a = ph[0][0] - 0.12; b = ph[-1][1] + 0.18
        if i + 1 < len(lines): b = min(b, lines[i + 1][0][0] - 0.05)
        a = max(a, 0)
        clip = x[int(a * sr):int(b * sr)]
        clip = resample_poly(clip, SR, sr)
        fade = int(0.012 * SR)
        clip[:fade] *= np.linspace(0, 1, fade); clip[-fade:] *= np.linspace(1, 0, fade)
        st = int((a + shift) * SR)
        out[st:st + len(clip)] += clip
        cues['lines'].append({'text': script.LINES[i], 'start': ph[0][0] + shift, 'end': ph[-1][1] + shift,
                              'phrases': [[p[0] + shift, p[1] + shift] for p in ph]})
    # gentle clean-up: rumble high-pass
    sos = butter(2, 70, 'hp', fs=SR, output='sos')
    out = sosfilt(sos, out)
    end = cues['lines'][-1]['end']
    cues['vo_end'] = end
    out = out[:int(SR * (end + 1.0))]
    w = wave.open('build/vo/narration.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    json.dump(cues, open('build/timeline.json', 'w'), indent=1)
    for i, l in enumerate(cues['lines']):
        print(f"L{i+1} {l['start']:6.2f}-{l['end']:6.2f}  " + '  '.join(f'[{a:.2f}-{b:.2f}]' for a, b in l['phrases']) + '  ' + l['text'][:50])
    return cues

if __name__ == '__main__':
    build()
