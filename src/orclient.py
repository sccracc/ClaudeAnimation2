"""Tiny OpenRouter client with cost tracking (hard cap enforced locally)."""
import os, json, base64, time, requests, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COSTLOG = os.path.join(ROOT, 'build', 'openrouter_costs.jsonl')
HARD_CAP = 5.00
SOFT_CAP = 1.50   # our own much lower working budget

def _key():
    k = os.environ.get('OPENROUTER_API_KEY')
    if not k:
        for line in open(os.path.join(ROOT, '.env')):
            if line.startswith('OPENROUTER_API_KEY='):
                k = line.strip().split('=', 1)[1]
    return k

def spent():
    tot = 0.0
    if os.path.exists(COSTLOG):
        for line in open(COSTLOG):
            tot += json.loads(line).get('cost', 0) or 0
    return tot

def _log(model, purpose, usage, gid):
    cost = (usage or {}).get('cost', 0) or 0
    os.makedirs(os.path.dirname(COSTLOG), exist_ok=True)
    with open(COSTLOG, 'a') as f:
        f.write(json.dumps({'t': time.time(), 'model': model, 'purpose': purpose, 'cost': cost, 'id': gid}) + '\n')
    print(f'[openrouter] {purpose}: ${cost:.5f}  (running total ${spent():.4f})')
    return cost

def _check(est):
    if spent() + est > SOFT_CAP:
        raise RuntimeError(f'Budget guard: spent {spent():.3f} + est {est} > {SOFT_CAP}')

def tts(text, out_wav, voice='cedar', model='openai/gpt-audio', instructions='', purpose='tts', est=0.05):
    _check(est)
    body = {"model": model, "modalities": ["text", "audio"], "audio": {"voice": voice, "format": "pcm16"}, "stream": True,
            "messages": [{"role": "system", "content": instructions},
                         {"role": "user", "content": text}]}
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                      headers={"Authorization": f"Bearer {_key()}"}, json=body, stream=True, timeout=300)
    r.raise_for_status()
    pcm = b''; transcript = ''; usage = None; gid = None
    for line in r.iter_lines():
        if not line: continue
        line = line.decode()
        if not line.startswith('data: '): continue
        data = line[6:]
        if data == '[DONE]': break
        j = json.loads(data)
        if 'error' in j: raise RuntimeError(j)
        gid = j.get('id', gid)
        if j.get('usage'): usage = j['usage']
        for ch in j.get('choices', []):
            a = ch.get('delta', {}).get('audio')
            if a:
                if a.get('data'): pcm += base64.b64decode(a['data'])
                if a.get('transcript'): transcript += a['transcript']
    _log(model, purpose, usage, gid)
    w = wave.open(out_wav, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm); w.close()
    return transcript

def chat(model, messages, purpose='chat', est=0.01, **kw):
    _check(est)
    body = {"model": model, "messages": messages}
    body.update(kw)
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                      headers={"Authorization": f"Bearer {_key()}"}, json=body, timeout=600)
    j = r.json()
    if 'error' in j: raise RuntimeError(j)
    _log(model, purpose, j.get('usage'), j.get('id'))
    return j

def audio_b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()
