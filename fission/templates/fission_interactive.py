#!/usr/bin/env python3
import argparse
import traceback
from pathlib import Path

try:
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--pipe", "-p", required=True)
    parser.add_argument("--name", "-n", required=False)
    args = parser.parse_args()

    pipe = Path(args.pipe.strip())
    fd = open(pipe, 'w')

    print(f"This is the interactive console for {args.name}.")

    if args.name: 
        name = args.name.strip()
    else:
        name = "Interactive"

    while True:

        data = input(f"{name} -> ") + "\n"
        fd.write(data)
        fd.flush()
except Exception as e:
    traceback.print_exc()
    input("Error occured, enter to close...")