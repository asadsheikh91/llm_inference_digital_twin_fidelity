"""Send one OpenAI-style chat request with one base64 image to a local vLLM server and print the raw JSON response."""
import base64, json, sys, time, urllib.request

model, image_path = sys.argv[1], sys.argv[2]
b64 = base64.b64encode(open(image_path, "rb").read()).decode()
body = {
    "model": model,
    "max_tokens": 48,
    "temperature": 0.0,
    "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        {"type": "text", "text": "Describe the shapes and colors in this image."},
    ]}],
}
req = urllib.request.Request("http://localhost:8000/v1/chat/completions",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
t0 = time.time()
with urllib.request.urlopen(req, timeout=300) as r:
    status, resp = r.status, r.read().decode()
print(f"HTTP {status} elapsed_s {time.time() - t0:.3f}")
print(resp)
