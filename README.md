# GreenWave Traffic Simulation

A Python-based traffic simulation system that implements various traffic light control algorithms including fixed timing cycles, adaptive algorithms, and green wave algorithms optimized for energy consumption and pollution reduction.

## Features

- **Multiple Traffic Control Algorithms**: Fixed timing cycles, adaptive algorithms, and green wave algorithms
- **Interactive GUI**: Pygame-based graphical interface with real-time simulation visualization
- **Network Analysis**: Graph-based traffic network modeling using NetworkX
- **Statistics and Analysis**: Comprehensive data collection and CSV export functionality
- **Configurable Settings**: User-friendly settings interface for algorithm and simulation parameters

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MrLegiongame/GreenWave.git
   cd GreenWave
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```
   
4. **Open the IDE and Press Install requesments**

5. **Run main.py in folder Code/**

## Usage

1. **Main Menu**: Navigate between different application screens
2. **Settings**: Configure simulation parameters, algorithms, and maps
3. **Simulation**: Run traffic simulations with real-time visualization
4. **Statistics**: View and export simulation results and performance metrics

## Algorithms

- **Fixed Timing Cycle**: Traditional traffic light control with predetermined timing
- **Adaptive Algorithm**: Dynamic traffic light control based on vehicle counts
- **Green Wave (Energy)**: Optimized for energy consumption reduction
- **Green Wave (Pollution)**: Optimized for pollution reduction
