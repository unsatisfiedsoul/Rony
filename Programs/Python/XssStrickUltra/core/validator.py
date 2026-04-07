def detect_context(response, payload):
    if payload in response:
        return "html"

    if payload.replace("<", "&lt;") in response:
        return "encoded"

    if payload.lower() in response.lower():
        return "reflected"

    return "none"
