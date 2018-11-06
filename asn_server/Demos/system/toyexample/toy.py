import sys
import argparse
from time import sleep

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--inputs", "-i", action="append")
    parser.add_argument("--outputs", "-o", action="append")
    args = parser.parse_args()

    i = 0
    while True:
        i += 1
        print(i)
        sys.stdout.flush()
        sleep(1)
