import typer
from calculator import Calculator

app = typer.Typer()
calc = Calculator()


@app.command()
def add(a: float, b: float):
    """Add two numbers."""
    typer.echo(calc.add(a, b))


@app.command()
def sub(a: float, b: float):
    """Subtract two numbers."""
    typer.echo(calc.subtract(a, b))


@app.command()
def mul(a: float, b: float):
    """Multiply two numbers."""
    typer.echo(calc.multiply(a, b))


@app.command()
def div(a: float, b: float):
    """Divide two numbers."""
    try:
        result = calc.divide(a, b)
        typer.echo(result)
    except ZeroDivisionError as exc:
        typer.echo(f"Error: {exc}")


if __name__ == "__main__":
    app()
