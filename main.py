import argparse

URL = "https://127.0.0.1:5000"

parser = argparse.ArgumentParser()
parser.add_argument("--package")
args = parser.parse_args()

package = args.package
print(package)