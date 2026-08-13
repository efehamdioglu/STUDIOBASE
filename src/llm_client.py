import json
import os

_anthropic_client = None


def get_provider() -> str:
    """LLM sağlayıcısı: 'ollama' (ücretsiz, yerel), 'gemini' (ücretsiz, bulut) veya 'anthropic' (API key gerektirir).
    Sağlayıcı değiştirmek tek bir env değişkeni (LLM_PROVIDER) ile yapılır — orkestratör
    ve ajan kodu hiç değişmeden aynı kalır."""
    return os.environ.get("LLM_PROVIDER", "ollama").strip().lower()


def get_default_model() -> str:
    prov = get_provider()
    if prov == "ollama":
        return os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:3b")
    elif prov == "gemini":
        return os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic

        _anthropic_client = anthropic.Anthropic()
    return _anthropic_client


def _call_anthropic(
    system_prompt: str, user_message: str, model: str, output_schema: dict | None, max_tokens: int
) -> str | dict:
    client = _get_anthropic_client()
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }
    if output_schema is not None:
        kwargs["output_config"] = {
            "format": {"type": "json_schema", "schema": output_schema}
        }

    response = client.messages.create(**kwargs)

    text = next((b.text for b in response.content if b.type == "text"), "")
    if output_schema is not None:
        return json.loads(text)
    return text


def _call_ollama(
    system_prompt: str, user_message: str, model: str, output_schema: dict | None, max_tokens: int
) -> str | dict:
    import ollama

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        format=output_schema if output_schema is not None else None,
        options={"num_predict": max_tokens},
    )
    content = response["message"]["content"]
    if output_schema is not None:
        return json.loads(content)
    return content


def _clean_schema_for_gemini(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return schema
    cleaned = {}
    for k, v in schema.items():
        if k == "additionalProperties":
            continue
        if isinstance(v, dict):
            cleaned[k] = _clean_schema_for_gemini(v)
        elif isinstance(v, list):
            cleaned[k] = [_clean_schema_for_gemini(item) if isinstance(item, dict) else item for item in v]
        else:
            cleaned[k] = v
    return cleaned


def _call_gemini(
    system_prompt: str, user_message: str, model: str, output_schema: dict | None, max_tokens: int
) -> str | dict:
    import urllib.request
    import urllib.error

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY tanımlı değil. Lütfen proje kökündeki .env dosyanıza "
            "Gemini API anahtarınızı ekleyin."
        )

    if "gemini" not in model:
        model = "gemini-3.5-flash-lite"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    generation_config = {
        "maxOutputTokens": max_tokens,
        "temperature": 0.7
    }
    if output_schema is not None:
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = _clean_schema_for_gemini(output_schema)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": generation_config
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            if output_schema is not None:
                return json.loads(text)
            return text
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            err_desc = err_json["error"]["message"]
        except Exception:
            err_desc = err_msg
        raise RuntimeError(f"Gemini API hatası ({e.code}): {err_desc}") from e
    except Exception as e:
        raise RuntimeError(f"Gemini çağrısı sırasında beklenmedik hata: {e}") from e


def call_agent(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    output_schema: dict | None = None,
    max_tokens: int = 4000,
) -> str | dict:
    """Bir ajanı çağırır. output_schema verilirse yapılandırılmış JSON döner
    (dict), aksi halde düz metin döner (str).
    """
    provider = get_provider()
    model = model or get_default_model()

    if provider == "ollama":
        return _call_ollama(system_prompt, user_message, model, output_schema, max_tokens)
    elif provider == "gemini":
        return _call_gemini(system_prompt, user_message, model, output_schema, max_tokens)
    return _call_anthropic(system_prompt, user_message, model, output_schema, max_tokens)
