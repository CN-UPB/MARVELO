#!/usr/bin/env python3
import sys

def main():
    network = sys.argv[1]
    try:
        from fission.manager import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import FISSION. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()