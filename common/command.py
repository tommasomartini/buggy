NUM_COMMANDS = 4


def encode(commands):
    """Encodes a list of binary commands into a numeric value.

    Example:
        [1, 0, 1, 0]
         |  |  |  +-> 0 * 2^0 = 0 +
         |  |  +----> 1 * 2^1 = 2 +
         |  +-------> 0 * 2^2 = 0 +
         +----------> 1 * 2^3 = 8 =
                               10
    """
    data = 0
    for pos_idx, val in enumerate(commands, start=1):
        data += val << (NUM_COMMANDS - pos_idx)
    return data


def decode(command_code):
    """Decodes a numeric value into a list of binary commands.

    Example:
        10 -> [1, 0, 1, 0]
    """
    commands = [0] * NUM_COMMANDS
    mask = 1
    for shift in range(NUM_COMMANDS):
        commands[NUM_COMMANDS - shift - 1] = mask & (command_code >> shift)
    return commands
