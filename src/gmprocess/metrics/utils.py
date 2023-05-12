def component_to_channel(channel_names):
    """Dictionary with mapping from channel name to component.

    Args:
        channel_names (list):
            List of strings for channel names, e.g., ["HNZ", "HNN", "HNE"].
    """
    channel_names = sorted(channel_names)
    channel_dict = {}
    reverse_dict = {}
    channel_number = 1
    for channel_name in channel_names:
        if channel_name.endswith("Z"):
            channel_dict["Z"] = channel_name
        else:
            cname = "H%i" % channel_number
            channel_number += 1
            channel_dict[cname] = channel_name

    reverse_dict = {v: k for k, v in channel_dict.items()}
    return (channel_dict, reverse_dict)
