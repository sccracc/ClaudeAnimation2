"""Generate the score with Google Lyria 3 Pro via OpenRouter ($0.08 per track). Audio output requires streaming."""
import os, sys, json, base64, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orclient

def generate(prompt, out, model='google/lyria-3-pro-preview'):
    orclient._check(0.1)
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {orclient._key()}"},
                      json={"model": model, "modalities": ["text", "audio"], "audio": {"format": "mp3"}, "stream": True,
                            "messages": [{"role": "user", "content": prompt}]}, stream=True, timeout=900)
    chunks, usage, gid = [], None, None
    for line in r.iter_lines():
        if not line or not line.startswith(b'data: '): continue
        d = line[6:].decode()
        if d.strip() == '[DONE]': break
        j = json.loads(d)
        if 'error' in j: raise RuntimeError(j)
        gid = j.get('id', gid)
        if j.get('usage'): usage = j['usage']
        for ch in j.get('choices', []):
            a = ch.get('delta', {}).get('audio')
            if a and a.get('data'): chunks.append(a['data'])
    orclient._log(model, 'music', usage, gid)
    open(out, 'wb').write(base64.b64decode(''.join(chunks)))

if __name__ == '__main__':
    root = orclient.ROOT
    generate(open(os.path.join(root, 'assets', 'audio', 'music_prompt.txt')).read(), os.path.join(root, 'assets', 'audio', 'music_lyria.mp3'))
