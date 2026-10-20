import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

SYSTEM_PROMPT = ("You are a friendly class assistant for students. "
                 "Explain things simply, in short steps, with a quick example.")

def index(request):
    return render(request, "assistant/index.html")

def service_worker(request):
    # Served from the site root so the worker can control the whole app
    return render(request, "assistant/sw.js", content_type="application/javascript")

@require_POST
def chat(request):
    try:
        prompt = json.loads(request.body).get("prompt", "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)
    if not prompt:
        return JsonResponse({"error": "Please enter a question."}, status=400)

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    # Main model first, then a backup if Google is busy
    models = [settings.GEMINI_MODEL, "gemini-3.5-flash-lite"]
    last_error = ""

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(2):
            try:
                r = requests.post(url, json=payload, timeout=30,
                                  headers={"x-goog-api-key": settings.GEMINI_API_KEY or ""})
            except Exception as e:
                last_error = repr(e)
                break
            if r.status_code == 200:
                try:
                    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return JsonResponse({"reply": text})
                except (KeyError, IndexError):
                    last_error = "Empty response from model."
                    break
            print("GEMINI ERROR:", model, r.status_code, r.text[:300])
            last_error = f"[{r.status_code}] {r.text[:200]}"
            if r.status_code in (429, 500, 503) and attempt == 0:
                time.sleep(2)      # wait, then retry once
                continue
            break                  # try the next model

    msg = "The AI is busy right now. Please try again in a moment."
    if settings.DEBUG:
        msg += " " + last_error
    return JsonResponse({"error": msg}, status=502)