import numpy as np
from collections import deque
import shutil
import argparse
from typing import List, Optional

tr = 2

class Vertex:
    def __init__(self, ids, tree_size, depth):
        self.id = ids
        self.tree_size = tree_size
        self.orig_tree_size = tree_size
        self.depth = depth
        self.rcv_count = 0
        self.rcv_color = 0
        self.snd_color = 0
        self.snd_control = False
        self.children = []


def print_tree(root: Vertex):
    def interval(v: Vertex):
        size = getattr(v, "orig_size", v.tree_size)
        return (v.id, v.id + size - 1, size)

    def node_parts(v: Vertex):
        _, _, size = interval(v)

        meta = []
        if size != 1:
            meta.append(f"n={size}")
        if v.depth != 0:
            meta.append(f"d={v.depth}")
        if v.children:
            meta.append(f"c={len(v.children)}")

        head = f"PE {v.id}"
        tail = f""
        if meta:
            tail += f" ({', '.join(meta)})"

        return head, tail

    rows = []

    def dfs(v: Vertex, guide: str, is_last: bool, is_root: bool = False):
        head, tail = node_parts(v)

        if is_root:
            left = f"  {head}"
            tail+= f"\t(root)"
        else:
            branch = "└── " if is_last else "├── "
            left = f"{guide}{branch}{head}"

        rows.append((left, tail))

        next_guide = guide + ("    " if is_last else "│   ")
        for i, ch in enumerate(v.children):
            dfs(ch, next_guide, i == len(v.children) - 1)

    dfs(root, "", True, is_root=True)

    width = max(len(left) for left, _ in rows)
    print(f"Generated tree:")
    for left, tail in rows:
        print(f"{left.ljust(width)}{tail}")
    print("(id, n, d) = (PE id, subtree size, depth)")


def print_pe_summary(all_pes: List[Optional[Vertex]]):
    rows = []
    for i, pe in enumerate(all_pes):
        if pe is None:
            rows.append({
                "pe": str(i),
                "children": "<None>",
                "rcv_cnt": "",
                "snd_ctrl": "",
                "snd_color": "",
                "rcv_color": "",
            })
        else:
            rows.append({
                "pe": str(i),
                "children": str([c.id for c in pe.children]),
                "rcv_cnt": str(pe.rcv_count),
                "snd_ctrl": str(pe.snd_control),
                "snd_color": str(pe.snd_color),
                "rcv_color": str(pe.rcv_color),
            })

    headers = {
        "pe": "PE",
        "children": "children",
        "rcv_cnt": "rcv_cnt",
        "snd_ctrl": "snd_ctrl",
        "snd_color": "snd_color",
        "rcv_color": "rcv_color",
    }

    widths = {}
    for key, title in headers.items():
        widths[key] = max(len(title), max(len(row[key]) for row in rows))

    print("\nPer-PE summary:")
    header_line = (
        f"{headers['pe']:<{widths['pe']}}  "
        f"{headers['children']:<{widths['children']}}  "
        f"{headers['rcv_cnt']:>{widths['rcv_cnt']}}  "
        f"{headers['snd_ctrl']:>{widths['snd_ctrl']}}  "
        f"{headers['snd_color']:>{widths['snd_color']}}  "
        f"{headers['rcv_color']:>{widths['rcv_color']}}"
    )
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        print(
            f"{row['pe']:<{widths['pe']}}  "
            f"{row['children']:<{widths['children']}}  "
            f"{row['rcv_cnt']:>{widths['rcv_cnt']}}  "
            f"{row['snd_ctrl']:>{widths['snd_ctrl']}}  "
            f"{row['snd_color']:>{widths['snd_color']}}  "
            f"{row['rcv_color']:>{widths['rcv_color']}}"
        )

def insert_line_at(file_name, line_number, text):
    """
    Insert a line into a file at a specific line number.

    :param file_name: The name of the file to be modified.
    :param line_number: The line number at which to insert the new line (1-based index).
    :param text: The text to be inserted.
    """
    with open(file_name, 'r') as file:
        lines = file.readlines()

    # Adjust the line number to be zero-indexed
    line_number -= 1

    # Ensure the specified line number is within the file's length
    if line_number < 0 or line_number > len(lines):
        print("Error: line number out of range")
        return

    # Insert the new line
    lines.insert(line_number, text + '\n')

    # Write the modified lines back to the file
    with open(file_name, 'w') as file:
        file.writelines(lines)


def insert_lines_at(file_name, line_number, lines_to_insert):
    """
    Insert multiple lines into a file at a specific line number.

    :param file_name: The name of the file to be modified.
    :param line_number: The line number at which to insert the new lines (1-based index).
    :param lines_to_insert: A list of lines to be inserted.
    """
    with open(file_name, 'r') as file:
        lines = file.readlines()

    # Adjust the line number to be zero-indexed
    line_number -= 1

    # Ensure the specified line number is within the file's length
    if line_number < 0 or line_number > len(lines):
        print("Error: line number out of range")
        return

    # Prepare the lines to be inserted with newline characters
    lines_to_insert = [line + '\n' for line in lines_to_insert]

    # Insert the new lines
    lines[line_number:line_number] = lines_to_insert

    # Write the modified lines back to the file
    with open(file_name, 'w') as file:
        file.writelines(lines)

def process_pe(pe, all_pes):
    all_pes[pe.id] = pe
    pe.rcv_count = len(pe.children)
    # print(f'id: {pe.id}, rcv count: {pe.rcv_count}, snd color: {pe.snd_color}, rcv color: {pe.rcv_color}')
    if (len(pe.children) == 0):	
        return
    for child in pe.children:
        child.snd_color = pe.rcv_color
        child.rcv_color = pe.snd_color
    pe.children[-1].snd_control = True

    for child in pe.children:
        process_pe(child, all_pes)

def lower_bound(P, B, verbose=False, summary=False, tree=False):
    # dp[receiver, depth] = minimum energy to reduce a scalar over `receiver` PEs with `depth` limit
    dp = np.array([[np.inf for _ in range(P + 1)] for _ in range(P + 1)])
    # base cases (for 0 or 1 receiver, no energy needed)
    dp[0, :] = 0
    dp[1, :] = 0

    # for each possible number of receivers
    for receiver in range(2, P + 1):
        # for each possible depth (increasing)
        for d in range(1, P + 1):
            # dp[receiver, d] = minimum energy to reduce `receiver` PEs using depth <= d.
            # If a solution fits within depth <= d-1, it also fits within depth <= d,
            # so allowing one more depth level cannot increase the minimum energy.
            dp[receiver, d] = dp[receiver, d-1]
            for sender in range(1, receiver):
                dp[receiver, d] = min(
                    dp[receiver, d],
                    dp[sender, d - 1] + dp[receiver - sender, d] + receiver - sender
                )
    if verbose:
        print("DP Table:")
        print("#r \\ d\t|", end="")
        for d in range(P + 1):
            print(f"{d}\t", end="")
        print("\n" + "-" * (8 * (P + 2)))
        for receiver in range(P + 1):
            print(f"{receiver}: ", end="\t|")
            for d in range(P + 1):
                if dp[receiver, d] == np.inf:
                    print("inf", end="\t")
                else:
                    print(f"{int(dp[receiver, d])}", end="\t")
            print()
        print()


    dp_copied = np.array(dp[P], copy=True)
    if verbose:
        print("Cost with vector length B:")
        print("d\t dp[P,d]\t dp_copied[d]")
        print("-" * 40)
    for d in range(P + 1):
        dp_copied[d] = (B * dp_copied[d])/max(1, P - 1) + P - 1 + d * (2 * tr + 1)
        if verbose:
            energy_str = "inf" if np.isinf(dp[P][d]) else f"{int(dp[P][d])}"
            score_str  = "inf" if np.isinf(dp_copied[d]) else f"{dp_copied[d]:.6f}"
            print(f"{d}\t {energy_str:>7}\t {score_str:>12}")

    cur_d = np.argmin(dp_copied)
    if verbose:
        print(f"Optimal depth: {cur_d}, with cost: {dp_copied[cur_d]:.6f}\n")


    root = Vertex(0, P, cur_d)
    root.snd_control = False
    root.rcv_color = 1
    pes = deque()
    pes.append(root)

    while pes:
        pe = pes.popleft()
        while (pe.tree_size > 1):
            for sender in range(1, pe.tree_size):
                if (dp[pe.tree_size, pe.depth] == dp[sender, pe.depth - 1] + dp[pe.tree_size - sender, pe.depth] + pe.tree_size - sender):
                    sender_vertex = Vertex(pe.id + pe.tree_size - sender, sender, pe.depth - 1)
                    pe.children.append(sender_vertex)
                    pe.tree_size -= sender
                    pes.append(sender_vertex)
                    break
        pe.children.reverse()

    if verbose or tree:
        print_tree(root)

    all_pes : List[Optional[Vertex]] = [None for _ in range(P)]
    process_pe(root, all_pes)

    if verbose or summary:
        print_pe_summary(all_pes)

    total_lines = []
    new_file_name = 'modules/pre_order_runtime.csl'
    shutil.copy("modules/pre_order_runtime_base.csl", new_file_name)
    for i in range(P):
        pe = all_pes[i]
        if pe is None:
            continue
        out_color        = "color_1" if (pe.snd_color == 0) else "color_2"
        in_color         = "color_2" if (pe.snd_color == 0) else "color_1"
        snd_control      = "true"    if (pe.snd_control)    else "false"
        out_color_line   = '        out_color = {};'.format(out_color)
        in_color_line    = '        in_color = {};'.format(in_color)
        rcv_count_line   = '        rcv_cnt = {};'.format(pe.rcv_count)
        snd_control_line = '        is_ctrl = {};'.format(snd_control)
        if_line          = ' if (pe_id == {}) '.format(i) + '{'
        end_if_line      = ' }'
        total_lines += [if_line, out_color_line, in_color_line, rcv_count_line, snd_control_line, end_if_line]
    with open(new_file_name, "r") as file:
        copied_lines = file.readlines()

    insert_line = next(
        idx for idx, line in enumerate(copied_lines, start=1)
        if "rev_id = NUM_PES - pe_id - 1;" in line
    ) + 1

    insert_lines_at(new_file_name, insert_line, total_lines)

def main():
    parser = argparse.ArgumentParser(description="Greet two people by their names.")
    parser.add_argument("P", type=int, help="Number of PEs")
    parser.add_argument("B", type=int, help="Vector Length")
    parser.add_argument("-t", "--tree", default=False, action="store_true", help="Print the generated tree")
    parser.add_argument("-s", "--summary", default=False, action="store_true", help="Print a summary of each PE's role in the reduction")
    parser.add_argument("-v", "--verbose", default=False, action="store_true", help="Print the generated tree and DP table")
    args = parser.parse_args()

    lower_bound(args.P, args.B, args.verbose, args.summary, args.tree)

if __name__ == "__main__":
    main()
