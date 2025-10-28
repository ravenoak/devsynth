import typer
from counter import Counter

app = typer.Typer()
counter = Counter()


@app.command()
def analyze(file: str):
    """Display counts for the given file."""
    try:
        text = open(file, encoding="utf-8").read()
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}")
        raise
    lines = counter.count_lines(text)
    words = counter.count_words(text)
    chars = counter.count_chars(text)
    typer.echo(f"Lines: {lines}\nWords: {words}\nChars: {chars}")


if __name__ == "__main__":
    app()
