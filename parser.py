import argparse

def read_grammar(file):
    content = []
    with open(file, 'r') as f:
        for line in f:
            content.append(line)
    print(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("grammar", help="Grammar file to be utilized")
    parser.add_argument("inputfile", help="Input file to test membership")
    
    args = parser.parse_args()
    print(args.grammar)
    print(args.inputfile)
    
    
if __name__ == "__main__":
    main()