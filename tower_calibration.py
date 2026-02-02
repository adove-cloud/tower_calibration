#!/usr/bin/env python3

"""
This script generates a GDSII (GDS) file for e-beam lithography 
calibration towers, often used for proximity effect correction (PEC) testing.

It creates a "Top" cell containing four patterns with different fill densities:
- 100% fill (a solid square with a center line gap)
- 50% fill (a grating of lines)
- 25% fill (a grating of lines with larger spacing)
- 0% fill (a single, isolated line)

The script prompts the user for three key parameters:
1.  Output Filename: The name of the GDS file to be created.
2.  Beta Value: The proximity effect backscattering parameter (in microns), 
    typically derived from a TRACER or similar simulation.
3.  Linewidth: The target critical dimension (CD) for the lines (in nanometers).
"""

import gdstk
import math

def get_user_input():
    """
    Prompts the user for required inputs and validates them.
    
    Returns:
        tuple: (filename, beta, line_size)
               filename (str): The validated output GDS filename.
               beta (float): The beta value in microns.
               line_size (float): The linewidth in microns.
    """
    # 1. Get Filename
    filename = input("Enter the output GDS filename (e.g., my_towers.gds): ")
    if not filename.lower().endswith('.gds'):
        filename += '.gds'
        print(f"Filename appended with .gds: {filename}")

    # 2. Get Beta Value
    while True:
        try:
            beta_str = input("Enter the beta value (from TRACER, in microns): ")
            beta = float(beta_str)
            if beta <= 0:
                print("Error: Beta value must be a positive number.")
            else:
                break
        except ValueError:
            print("Error: Invalid input. Please enter a number (e.g., 9.4).")

    # 3. Get Linewidth
    while True:
        try:
            line_size_nm_str = input("Enter the target linewidth in nanometers (e.g., 80): ")
            line_size_nm = float(line_size_nm_str)
            if line_size_nm <= 0:
                print("Error: Linewidth must be a positive number.")
            else:
                break
        except ValueError:
            print("Error: Invalid input. Please enter a number (e.g., 80).")

    # Convert nm to microns for GDS generation
    line_size = line_size_nm / 1000.0
    
    return filename, beta, line_size


def create_gds_towers(filename, beta, line_size):
    """
    Generates the GDS tower structures and saves them to a file.
    
    Args:
        filename (str): The name of the file to save.
        beta (float): The proximity parameter in microns.
        line_size (float): The target linewidth in microns.
    """
    print("\n--- Starting GDS Generation ---")
    
    # Initialize GDS library
    lib = gdstk.Library()

    # --- Calculations (from original notebook) ---
    # Pitch for 50% fill (line_size = space_size)
    pitch = 2 * line_size
    
    # Calculate square size based on 25% fill requirements
    # Pitch for 25% fill is 2 * pitch (line_size = 3 * line_size space)
    pitch_25 = 2 * pitch
    number_of_gratings_25_fill = math.ceil(4 * beta / pitch_25)
    print(f"Linewidth: {line_size*1000:.1f} nm ({line_size:.3f} um)")
    print(f"Beta: {beta:.2f} um")
    print(f"Calculated 25% fill gratings: {number_of_gratings_25_fill}")

    square_size = number_of_gratings_25_fill * pitch_25
    print(f"Calculated square size: {square_size:.3f} um")
    
    # Calculate number of gratings for 50% fill to match the square size
    number_of_gratings_50_fill = math.ceil(square_size / pitch)
    print(f"Calculated 50% fill gratings: {number_of_gratings_50_fill}")

    # --- Cell Definitions ---

    # Create the main cell that will hold everything
    cell = lib.new_cell("Top")

    # Create a reusable cell for a single line
    c_line = lib.new_cell("line")
    rect = gdstk.rectangle((-line_size / 2, -square_size / 2), 
                           (line_size / 2, square_size / 2))
    c_line.add(rect)

    # --- Pattern Assembly ---
    
    # Define vertical spacing for the towers
    # The gap between towers is 4 * beta
    y_gap = 4 * beta
    y_pos_100 = 0
    y_pos_50 = square_size + y_gap
    y_pos_25 = 2 * (square_size + y_gap)
    y_pos_0 = 3 * (square_size + y_gap)

    # 1. 100% fill section (at y=0)
    # One large rectangle with a gap for the center line
    array_100_fill = gdstk.rectangle((-square_size / 2, -square_size / 2 + y_pos_100),
                                     (square_size / 2, square_size / 2 + y_pos_100))
    # Gap is 3x the line size, centered at x=0
    center_fill_gap = gdstk.rectangle((-3 * line_size / 2, -square_size / 2 + y_pos_100),
                                      (3 * line_size / 2, square_size / 2 + y_pos_100), 
                                      layer=2) # Use a dummy layer for the boolean
    
    # Subtract the gap from the solid rectangle
    cell.add(*gdstk.boolean(array_100_fill, center_fill_gap, "not"))
    # Add the single center line
    cell.add(gdstk.Reference(c_line, origin=(0, y_pos_100)))

    # 2. 75% fill section (Skipped, as in original notebook)
    # ... (code commented out) ...

    # Calculate robust origins to center the arrays
    # This replaces the "magic number" offsets from the notebook,
    # ensuring the arrays are centered regardless of line size.
    origin_x_50 = -(number_of_gratings_50_fill - 1) * pitch / 2
    origin_x_25 = -(number_of_gratings_25_fill - 1) * pitch_25 / 2

    # 3. 50% fill section
    array_50_fill = gdstk.Reference(
        c_line,
        origin=(origin_x_50, y_pos_50),
        columns=number_of_gratings_50_fill,
        spacing=(pitch, 0)
    )

    # 4. 25% fill section
    array_25_fill = gdstk.Reference(
        c_line,
        origin=(origin_x_25, y_pos_25),
        columns=number_of_gratings_25_fill,
        spacing=(pitch_25, 0)
    )
         
    # 5. 0% fill section (single line)
    array_0_fill = gdstk.Reference(c_line, origin=(0, y_pos_0))

    # Add the arrays to the top cell
    cell.add(array_50_fill, array_25_fill, array_0_fill)

    # --- File Output ---
    lib.write_gds(filename)
    print(f"\nSuccessfully wrote GDS file to: {filename}")


if __name__ == "__main__":
    # This block runs only when the script is executed directly
    try:
        # Get inputs from the user
        fname, val_beta, val_line_size = get_user_input()
        
        # Generate the GDS file
        create_gds_towers(fname, val_beta, val_line_size)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")