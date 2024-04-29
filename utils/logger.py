from rich.console import Console

def get_log():
    console = Console()
    while True:
        yield console

logger = get_log()

def log():
    return next(logger)
