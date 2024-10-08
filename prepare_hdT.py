import numpy as np
import json
from utils import *  # Import utility functions from utils module

# Load configuration settings from a JSON file
with open("config.json", "r") as f:
    config = json.load(f)


def find_hdT(target_func_name, dy=None, l=None, r=None):
    """
    Calculate high-dimensional T values for a given target function.

    Args:
        target_func_name (str): The name of the target function.
        dy (float, optional): Step size for selecting elements. Defaults to None.
        l (float, optional): Left boundary for input range. Defaults to None.
        r (float, optional): Right boundary for input range. Defaults to None.

    Returns:
        hdT (dict): A dictionary containing the high-dimensional T parameters.
    """
    print(f"Finding hdT for {target_func_name}...")

    # Retrieve the target function from the global namespace
    target_func = globals()[target_func_name]

    # Get the path for storing hdT values
    hdT_path = config["hdT_path"]

    # Use default values from the config file if not provided
    if dy is None:
        dy = config["dy"]
        l = config["l"]
        r = config["r"]
        save_path = f"{hdT_path}{target_func_name}.pt"  # Default save path
    else:
        save_path = f"{hdT_path}{target_func_name}_{dy}_{l}_{r}.pt"  # Custom save path

    # Generate input range and apply the target function
    x = np.arange(l, r, 0.001)  # Create a range of input values
    y = target_func(x)  # Apply the target function

    # Normalize y-values to start from zero
    m = np.min(y)
    b = -m
    y += b

    # Calculate integer and fractional bits for fixed-point representation
    M = np.max(y)
    i_bit = int(np.ceil(np.log2(M)))
    f_bit = -int(np.floor(np.log2(dy)))
    K = i_bit + f_bit

    # Select elements from y with a step size of dy. It is not nessesary.
    idx, y = select_elements_by_step(y, dy)
    x = x[idx]  # Corresponding x values

    # Initialize d, h, and T arrays
    d = [0.0] + [2 ** (i_bit - i) for i in range(K)]
    h = [x]
    T = [0.0] + [np.inf for _ in range(K)]

    # Calculate h and T values for each time step
    for t in range(1, K + 1):
        v_at_t = np.array([inverse_f(target_func, i, b) for i in y])
        h.append(v_at_t)
        mask = y > d[t]
        y[mask] -= d[t]
        T[t] = np.min(v_at_t[mask]) if np.any(mask) else T[t]

    # Convert arrays to PyTorch tensors
    h = torch.tensor(np.array(h).T, dtype=torch.float32)
    d = torch.tensor(d, dtype=torch.float32)
    T = torch.tensor(T, dtype=torch.float32)

    # Create a dictionary of high-dimensional T parameters
    hdT = {
        "h": h,
        "d": d,
        "T": T,
        "b": b,
        "dy": dy,
        "K": K,
        "i_bit": i_bit,
        "f_bit": f_bit,
        "l": l,
        "r": r,
        "num_h": len(h),
    }

    # Save the hdT parameters to a file
    torch.save(hdT, save_path)

    # Print summary of the saved hdT parameters
    print(
        f"Saved hdT to {save_path}\ndy: {dy}\nK: {K}\ti_bit: {i_bit}\tf_bit: {f_bit}\nl: {l}\tr: {r}\tb: {b}\nnum_h: {len(h)}"
    )
    print("Done.\n" + "-" * 50)

    return hdT


if __name__ == "__main__":
    # Find and save hdT values for the sigmoid function
    find_hdT("sigmoid")
