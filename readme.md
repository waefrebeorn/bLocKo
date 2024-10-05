# bLocKo - The Puzzle Game

bLocKo is a puzzle game inspired by classic block-dropping games. It features various game modes, power-ups, and a scoring system, providing an engaging experience for players. The game is currently in development, with features and mechanics being refined over time.

## Features

- Multiple game modes:
  - **Marathon**: Play until you reach a game-over state.
  - **Sprint**: Complete as many lines as possible in a limited time.
  - **Ultra**: Similar to Sprint with a longer time limit.
  - **Pressure**: Clear lines quickly as the pressure builds.
- Variety of block shapes and colors.
- Power-ups to enhance gameplay.
- High score tracking.
- Customizable key bindings.

## Getting Started

### Prerequisites

Make sure you have Python 3.6 or later installed on your machine. You will also need to install the required packages listed in `requirements.txt`.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/waefrebeorn/bLocKo.git
   cd bLocKo
   ```

2. Set up a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

4. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

### Running the Game

To run the game, you can use the provided batch file:

- On Windows:

  ```bash
  run.bat
  ```

You can also run the game directly from the Python script:

```bash
python blocko.py
```

### Files in the Project

- `blocko.py`: Main game code.
- `high_scores.json`: Stores high scores for the game.
- `key_bindings.json`: Stores custom key bindings.
- `requirements.txt`: Lists the required Python packages.
- `run.bat`: Batch file to run the game.
- `setup.bat`: Batch file for setting up the environment.
- `nonfunctional checkpoint.py`: Contains previous development iterations.
- `oldblocko.py`: An earlier version of the game.

### Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have suggestions or improvements.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by classic puzzle games.
- Thanks to the community for support and feedback during development.
