import sys

import matplotlib.pyplot as plt
import numpy as np


def create_figure(path: str):
    """
    Create and save a sine wave plot to the specified file path.

    This function generates a matplotlib figure containing a sine wave plot
    with appropriate labels, grid, and legend, then saves it to the given path.

    Args:
        path (str): The file path where the figure should be saved.
                   Should include the desired file extension (e.g., .png, .pdf, .svg).

    Returns:
        None: The function saves the figure to disk but doesn't return anything.

    Example:
        create_figure("sine_wave.png")
    """
    # Create sample data
    x = np.linspace(0, 10, 100)
    y = np.sin(x)

    # Create the figure
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, "b-", label="sin(x)")
    plt.title("Example Sine Wave")
    plt.xlabel("x")
    plt.ylabel("sin(x)")
    plt.grid(True)
    plt.legend()

    # Save the figure
    plt.savefig(path)


def main():
    """
    Main entry point for the script that handles command line arguments.

    This function processes command line arguments to get the output path
    and calls create_figure to generate and save a sine wave plot.

    The script expects exactly one command line argument (the output path).
    If the wrong number of arguments is provided, it prints usage information
    and exits with status code 1.

    Args:
        None: Uses sys.argv to get command line arguments.

    Returns:
        None: Exits the program after creating the figure or on error.

    Raises:
        SystemExit: If incorrect number of command line arguments provided.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 hello.py <output-path>")
        sys.exit(1)

    create_figure(sys.argv[1])


if __name__ == "__main__":
    main()
