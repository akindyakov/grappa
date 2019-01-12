#!/usr/bin/env python3

import sys
import hashlib
import base64


class Keywords:
    NODE = "node"
    EDGE = "edge"
    PRINT = "print"
    SAVE = "save"
    EXIT = "exit"


class Edge:
    def __init__(self, src, dst, title):
        self.title = title
        self.src = src
        self.dst = dst

    def gen_hash(self):
        m = hashlib.md5()
        m.update(bytes(self.title, "utf-8"))
        m.update(bytes(self.src, "utf-8"))
        m.update(bytes(self.dst, "utf-8"))

        return base64.b32encode(
            m.digest()
        ).strip(b"=").decode("utf-8").lower()


class Node:
    def __init__(self, title):
        self.title = title

    def gen_hash(self):
        pref = list()
        for ch in self.title:
            chn = ord(ch)
            if chn > 0x60 and chn < 0x7b or chn > 0x40 and chn < 0x5b:
                pref.append(ch.lower())

        m = hashlib.md5()
        m.update(bytes(self.title, "utf-8"))

        # TODO: use z-base-32 here instead of base64
        return "".join(pref) + base64.b32encode(
            m.digest()
        ).strip(b"=").decode("utf-8").lower()


def verify_args(args, expected_num):
    if len(args) < expected_num:
        print(" err > wrong number of tokens")
        return False
    return True


def verify_node_exists(node_id, nodes):
    if node_id not in nodes:
        print(" err > no such node {}".format(node_id))
        return False
    return True


def insert_unique(dst, obj):
    full_hash = obj.gen_hash()
    for size in range(2, len(full_hash)):
        for pos in range(len(full_hash) - size):
            short_id = full_hash[pos: pos + size]
            if short_id not in dst:
                dst[short_id] = obj
                return short_id


class BraceCloser:
    def __init__(self, stream, title):
        self.stream = stream
        self.title = title

    def __enter__(self):
        self.stream.write(
            "{} {{\n".format(self.title)
        )

    def __exit__(self, *args):
        self.stream.write("}\n")


def print_graph(stream, nodes, edges):
    with BraceCloser(stream, "digraph Grappa"):
        for node_id, node in nodes.items():
            stream.write("""{} [label="{}"];\n""".format(node_id, node.title))
        stream.write("\n")
        for edge_id, edge in edges.items():
            stream.write("""{} -> {} [label="{}: {}"];\n""".format(edge.src, edge.dst, edge_id, edge.title))


if __name__ == "__main__":
    edges = dict()
    nodes = dict()
    for num, line in enumerate(sys.stdin):
        line = line.strip()
        args = line.split()
        if not verify_args(args, 1):
            continue

        if args[0] == Keywords.NODE:
            if not verify_args(args, 2):
                continue
            title = " ".join(args[1:])
            node_id = insert_unique(nodes, Node(title))
            print(" > new node: {}".format(node_id))
        elif args[0] == Keywords.EDGE:
            if not verify_args(args, 3):
                continue
            src = args[1]
            if not verify_node_exists(src, nodes):
                continue
            dst = args[2]
            if not verify_node_exists(dst, nodes):
                continue
            title = " ".join(args[3:])
            edge_id = insert_unique(edges, Edge(src, dst, title))
            print(" > new edge: {}".format(edge_id))
        elif args[0] == Keywords.PRINT:
            print_graph(sys.stdout, nodes, edges)
        elif args[0] == Keywords.SAVE:
            if not verify_node_exists(dst, 2):
                continue
            filename = args[1]
            with open(filename, "wb") as fout:
                print_graph(fout, nodes, edges)
            print(" > saved to {}".format(filename))
        elif args[0] == Keywords.EXIT:
            print(" > exit")
            break
        else:
            print(" err > unknown command {}".format(args[0]))
