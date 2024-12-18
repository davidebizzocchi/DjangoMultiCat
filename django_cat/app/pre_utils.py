
def get_version_from_file():
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "v0.0.0-unknown"