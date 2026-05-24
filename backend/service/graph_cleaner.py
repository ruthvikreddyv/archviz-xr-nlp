def clean_graph(contract):
    replacements = {
        "multi-head_add": "Multi-Head Attention",
        "norm": "Normalization",
        "self-attention": "Self Attention",
    }

    cleaned_nodes = []

    for node in contract.get("nodes", []):
        label = node.get("label", "")
        replacement = replacements.get(label.lower())

        if replacement:
            node["label"] = replacement

        cleaned_nodes.append(node)

    contract["nodes"] = cleaned_nodes
    return contract
