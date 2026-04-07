from rich.console import Console
from rich.live import Live
from rich.table import Table
import time

console = Console()

def dashboard(stats):
    with Live(refresh_per_second=2) as live:
        while True:
            table = Table(title="XSS-ULTRA Dashboard")

            table.add_column("Metric")
            table.add_column("Value")

            for k, v in stats.items():
                table.add_row(k, str(v))

            live.update(table)
            time.sleep(1)
