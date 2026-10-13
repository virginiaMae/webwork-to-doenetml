import re

def convert_perl_to_doenetml(perl_lines):
    doenetml = []
    in_setup = False
    in_text = False
    question_body = []  # List to store question body outside of <setup>

    for line in perl_lines:
        line = line.strip()

        # Skip empty lines or Perl comments
        if not line or line.startswith('#'):
            continue

        # Begin problem
        if "TEXT(beginproblem())" in line:
            doenetml.append("<question><title/>\n<setup>")
            in_setup = True
            continue

        # Extract question body from TEXT block and move outside <setup>
        if "BEGIN_TEXT" in line:
            in_text = True
            continue

        if in_text:
            if "END_TEXT" in line:
                in_text = False
                # Close the <setup> block and add the question body inside a <p> tag
                doenetml.append("</setup>")
                doenetml.append("<p>" + "\n".join(question_body) + "</p>")
                question_body = []  # Reset the question body
                continue
            question_body.append(line)

        # Show partial credit
        if re.match(r'^\$showPartialCorrectAnswers\s*=\s*1;', line):
            doenetml.append('<!-- matchPartial on the <answer> tag or <award> -->')
            continue

        # Random assignment -> selectFromSequence
        m = re.match(r'^\$(\w+)\s*=\s*random\(([^,]+),([^,]+),([^)]+)\);', line)
        if m:
            name, start, end, step = m.groups()
            doenetml.append(f'<selectFromSequence name="{name}" from="{start.strip()}" to="{end.strip()}" step="{step.strip()}"/>')
            continue

        # Compute(...) assignment -> number
        m = re.match(r'^\$(\w+)\s*=\s*Compute\("(.+)"\);', line)
        if m:
            name, expr = m.groups()
            doenetml.append(f'<number name="{name}">{expr}</number>')
            continue

        # Answer comparisons (ANS) - Create <answer> tag for user input
        m = re.match(r'^ANS\(\$(\w+)->cmp\(\)\);', line)
        if m:
            answer_name = m.group(1)
            # Add the <answer> tag with a corresponding <mathInput> for each answer
            doenetml.append(f'<answer name="{answer_name}"><mathInput name="mi{answer_name}" minWidth="100" unionFromU/></answer>')
            continue

        # END_TEXT closes setup block
        if "END_TEXT" in line and in_setup:
            doenetml.append("</setup>")
            in_setup = False
            continue

        # End of document
        if "ENDDOCUMENT" in line:
            doenetml.append("</question>")
            continue

        # Preserve any other line as comment
        doenetml.append(f"<!-- {line} -->")

    return "\n".join(doenetml)


def main():
    input_file = "sample_problem.pl"  # replace with your input
    output_file = "converted_problem.doenet"

    with open(input_file, 'r') as f:
        perl_lines = f.readlines()

    doenetml_output = convert_perl_to_doenetml(perl_lines)

    with open(output_file, 'w') as f:
        f.write(doenetml_output)

    print(f"Conversion complete. Output written to {output_file}")


if __name__ == "__main__":
    main()
