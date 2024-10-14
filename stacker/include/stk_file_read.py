def readtxt(file_path):
    """
    This function reads a text file and ignores lines that are either
    within triple double quotes (\"\"\")
    within triple single quotes (''')
    start with a hash (#)
    or are blank lines (including the last line if it's blank).
    Additionally, it trims a final newline character if it exists.
    """
    with open(file_path, "r") as file:
        lines = file.readlines()

    # State flags to track if the current line is within a block comment
    in_double_quote_comment = False
    in_single_quote_comment = False

    filtered_lines = []

    for line in lines:
        if line.strip().startswith(
            '"""'
        ):  # Check for the start and end of triple double quote block
            in_double_quote_comment = not in_double_quote_comment
            continue  # Skip the line with triple quotes
        if line.strip().startswith(
            "'''"
        ):  # Check for the start and end of triple single quote block
            in_single_quote_comment = not in_single_quote_comment
            continue  # Skip the line with triple quotes
        if (
            in_double_quote_comment or in_single_quote_comment
        ):  # Skip lines within block comments
            continue
        # if (
        #     line.strip().startswith("#") or not line.strip()
        # ):  # Skip lines that start with # or are blank lines (including the last line if it's blank)
        #     continue
        filtered_lines.append(line)

    # Trim the final newline character if it exists
    if filtered_lines and not filtered_lines[-1].strip():
        filtered_lines.pop()

    return "".join(filtered_lines).rstrip(
        "\n"
    )  # Remove trailing newline if it's the last character
