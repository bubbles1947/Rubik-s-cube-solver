from cube_ui import CubeApp


def main():
    
    print("Rubik's Cube Simulator")
    print()
    print("  Controls:")
    print("    R/L/U/D/F/B     →  Clockwise rotation")
    print("    Shift + key     →  Counter-clockwise rotation")
    print("    S               →  Scramble the cube")
    print("    Space           →  Solve the cube")
    print("    Z               →  Undo last move")
    print("    Esc             →  Reset to solved state")
    print()
    print("Starting the graphical interface for solver")
    print()

    app = CubeApp()
    app.run()


if __name__ == "__main__":
    main()

