"""Ask a cheap multimodal model (Gemini Flash via OpenRouter) to watch + listen to a low-res review copy and report problems."""
import os, sys, base64, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orclient, script

def review(video, prompt_extra='', model='google/gemini-3.8-flash'):
    small = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build', 'review_small.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vf', 'scale=960:540', '-c:v', 'libx264', '-crf', '30', '-preset', 'fast',
                    '-c:a', 'aac', '-b:a', '96k', small], check=True)
    b64 = base64.b64encode(open(small, 'rb').read()).decode()
    text = ("You are a demanding animation director and sound supervisor reviewing a finished ~59 second hand-made paper-collage animated short "
            f"about the topic: '{script.TOPIC}'. The narration script is:\n" + "\n".join(script.LINES) + "\n\n"
            "Watch AND listen carefully. Report concrete, timestamped problems only (no generic praise): "
            "(1) visual glitches, broken or blank frames, flicker, pops, objects clipping or cut off awkwardly, unreadable or misspelled text; "
            "(2) animation that feels stiff, too fast/slow, or confusing; transitions that feel abrupt; "
            "(3) visuals that do not match what the narrator is saying at that moment (sync); "
            "(4) audio: is narration always clearly above the music? any clipping, harsh or annoying sound effects, sudden loudness jumps, silence gaps, music ending awkwardly; "
            "(5) consistency of style. Finish with the 5 most valuable fixes, ordered by impact, and an overall score out of 10. " + prompt_extra)
    content = [{"type": "text", "text": text}, {"type": "video_url", "video_url": {"url": "data:video/mp4;base64," + b64}}]
    j = orclient.chat(model, [{"role": "user", "content": content}], purpose='video review', est=0.05)
    return j['choices'][0]['message']['content']

if __name__ == '__main__':
    print(review(sys.argv[1], ' '.join(sys.argv[2:])))
