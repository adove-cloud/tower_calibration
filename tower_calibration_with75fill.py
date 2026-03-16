#!/usr/bin/env python3

"""
This script generates a GDSII (GDS) file for e-beam lithography 
calibration towers, often used for proximity effect correction (PEC) testing.

It creates a "Top" cell containing patterns with different fill densities:
- 100% fill (a solid square with a center line gap)
- Custom fill (user-defined between 51% and 75%, optional)
- 50% fill (a grating of lines)
- 25% fill (a grating of lines with larger spacing)
- 0% fill (a single, isolated line)
"""

import gdstk
import math

def get_user_input():
    """
    Prompts the user for required inputs and validates them.
    
    Returns:
        tuple: (filename, beta, line_size, custom_fill)
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

    # 4. Get Custom Fill Percentage
    while True:
        try:
            custom_fill_str = input("Enter custom fill percentage between 51 and 75 (enter 0 to skip): ")
            custom_fill = float(custom_fill_str)
            if custom_fill == 0 or (51 <= custom_fill <= 75):
                break
            else:
                print("Error: Value must be 0, or between 51 and 75.")
        except ValueError:
            print("Error: Invalid input. Please enter a valid number.")

    # Convert nm to microns for GDS generation
    line_size = line_size_nm / 1000.0
    
    return filename, beta, line_size, custom_fill


def create_gds_towers(filename, beta, line_size, custom_fill):
    """
    Generates the GDS tower structures and saves them to a file.
    """
    print("\n--- Starting GDS Generation ---")
    
    # Initialize GDS library
    lib = gdstk.Library()

    # --- Calculations ---
    pitch = 2 * line_size
    pitch_25 = 2 * pitch
    
    number_of_gratings_25_fill = math.ceil(4 * beta / pitch_25)
    square_size = number_of_gratings_25_fill * pitch_25
    number_of_gratings_50_fill = math.ceil(square_size / pitch)

    # --- Cell Definitions ---
    cell = lib.new_cell("Top")
    c_line = lib.new_cell("line")
    rect = gdstk.rectangle((-line_size / 2, -square_size / 2), 
                           (line_size / 2, square_size / 2))
    c_line.add(rect)

    # --- Dynamic Y-Positioning ---
    y_gap = 4 * beta
    y_pos_100 = 0
    current_y = square_size + y_gap

    has_custom_block = custom_fill > 0
    
    if has_custom_block:
        y_pos_custom = current_y
        current_y += square_size + y_gap
        
        # Calculate specific parameters for the custom block
        pitch_custom = line_size / (custom_fill / 100.0)
        number_of_gratings_custom_fill = math.ceil(square_size / pitch_custom)
        origin_x_custom = -(number_of_gratings_custom_fill - 1) * pitch_custom / 2

    y_pos_50 = current_y
    current_y += square_size + y_gap
    
    y_pos_25 = current_y
    current_y += square_size + y_gap
    
    y_pos_0 = current_y

    # --- Pattern Assembly ---
    
    # 1. 100% fill section
    array_100_fill = gdstk.rectangle((-square_size / 2, -square_size / 2 + y_pos_100),
                                     (square_size / 2, square_size / 2 + y_pos_100))
    center_fill_gap = gdstk.rectangle((-3 * line_size / 2, -square_size / 2 + y_pos_100),
                                      (3 * line_size / 2, square_size / 2 + y_pos_100), 
                                      layer=2)
    cell.add(*gdstk.boolean(array_100_fill, center_fill_gap, "not"))
    cell.add(gdstk.Reference(c_line, origin=(0, y_pos_100)))

    # 2. Custom fill section (Conditional)
    if has_custom_block:
        array_custom_fill = gdstk.Reference(
            c_line,
            origin=(origin_x_custom, y_pos_custom),
            columns=number_of_gratings_custom_fill,
            spacing=(pitch_custom, 0)
        )
        cell.add(array_custom_fill)
        print(f"Added custom {custom_fill}% fill block.")
    else:
        print("Skipped custom fill block.")

    # Centering math for remaining gratings
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
         
    # 5. 0% fill section
    array_0_fill = gdstk.Reference(c_line, origin=(0, y_pos_0))

    # Add standard arrays to the top cell
    cell.add(array_50_fill, array_25_fill, array_0_fill)

    # --- File Output ---
    lib.write_gds(filename)
    print(f"\nSuccessfully wrote GDS file to: {filename}")


if __name__ == "__main__":
    try:
        fname, val_beta, val_line_size, val_custom_fill = get_user_input()
        create_gds_towers(fname, val_beta, val_line_size, val_custom_fill)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
