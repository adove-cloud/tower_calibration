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
    """
    print("\n--- Starting GDS Generation ---")
    
    # Initialize GDS library
    lib = gdstk.Library()

    # --- Calculations ---
    # Pitch for 50% fill (line_size = space_size)
    pitch = 2 * line_size
    
    # Pitch for 75% fill (line_size = 3/4 of pitch -> pitch = line_size / 0.75)
    pitch_75 = line_size / 0.75
    
    # Pitch for 25% fill is 2 * pitch (line_size = 1/4 of pitch)
    pitch_25 = 2 * pitch
    
    # Calculate square size based on 25% fill requirements (consistent with your original)
    number_of_gratings_25_fill = math.ceil(4 * beta / pitch_25)
    square_size = number_of_gratings_25_fill * pitch_25
    
    # Calculate counts for other gratings to match the square size footprint
    number_of_gratings_75_fill = math.ceil(square_size / pitch_75)
    number_of_gratings_50_fill = math.ceil(square_size / pitch)

    # --- Cell Definitions ---
    cell = lib.new_cell("Top")
    c_line = lib.new_cell("line")
    rect = gdstk.rectangle((-line_size / 2, -square_size / 2), 
                           (line_size / 2, square_size / 2))
    c_line.add(rect)

    # --- Pattern Assembly ---
    y_gap = 4 * beta
    # Calculate Y positions sequentially
    y_pos_100 = 0
    y_pos_75 = square_size + y_gap
    y_pos_50 = 2 * (square_size + y_gap)
    y_pos_25 = 3 * (square_size + y_gap)
    y_pos_0 = 4 * (square_size + y_gap)

    # 1. 100% fill section
    array_100_fill = gdstk.rectangle((-square_size / 2, -square_size / 2 + y_pos_100),
                                     (square_size / 2, square_size / 2 + y_pos_100))
    center_fill_gap = gdstk.rectangle((-3 * line_size / 2, -square_size / 2 + y_pos_100),
                                      (3 * line_size / 2, square_size / 2 + y_pos_100), 
                                      layer=2)
    cell.add(*gdstk.boolean(array_100_fill, center_fill_gap, "not"))
    cell.add(gdstk.Reference(c_line, origin=(0, y_pos_100)))

    # Centering math for the gratings
    origin_x_75 = -(number_of_gratings_75_fill - 1) * pitch_75 / 2
    origin_x_50 = -(number_of_gratings_50_fill - 1) * pitch / 2
    origin_x_25 = -(number_of_gratings_25_fill - 1) * pitch_25 / 2

    # 2. 75% fill section (NEWLY ADDED)
    array_75_fill = gdstk.Reference(
        c_line,
        origin=(origin_x_75, y_pos_75),
        columns=number_of_gratings_75_fill,
        spacing=(pitch_75, 0)
    )

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
         
    # 5. 0% fill section
    array_0_fill = gdstk.Reference(c_line, origin=(0, y_pos_0))

    # Add all arrays to the top cell
    cell.add(array_75_fill, array_50_fill, array_25_fill, array_0_fill)

    # --- File Output ---
    lib.write_gds(filename)
    print(f"\nSuccessfully wrote GDS file with 75% fill tower to: {filename}")


if __name__ == "__main__":
    # This block runs only when the script is executed directly
    try:
        # Get inputs from the user
        fname, val_beta, val_line_size = get_user_input()
        
        # Generate the GDS file
        create_gds_towers(fname, val_beta, val_line_size)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")