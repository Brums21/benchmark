import sys
import os

def open_file(file_name):

    dirname = os.getcwd()
    filename = os.path.abspath(os.path.join(dirname, file_name))
    
    print(f"Resolved file path: {filename}")
    
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist.")
        sys.exit(1)

    output_file_name = os.path.splitext(filename)[0] + "_cleaned" + os.path.splitext(filename)[1]
    
    print(f"Output file path: {output_file_name}")
    
    with open(filename, "r") as input_file:
        for line in input_file.readlines():
            if line.startswith("#"):
                continue
            original_line = line.split("\t")
            first_element = original_line[0].split(" ")[0] # nome do chromossoma
            rest_element = '\t'.join(original_line[1:])
            rest_element = first_element + "\t" + rest_element
            
            # dividir o output em varios ficheiros
            write_to_output(os.path.splitext(filename)[0] + "_cleaned_" + str(first_element[0:3]) + os.path.splitext(filename)[1], rest_element)


def write_to_output(filename, text):
    file = open(filename, 'a')
    file.write(text)
    file.close()


def main():
    if len(sys.argv) != 2:
        print("Incorrect number of arguments.")
        print("Usage:")
        print("\t./modify_output.py <input_file_to_be_analyzed>")
        return

    open_file(sys.argv[1])

if __name__ == "__main__":
    main()