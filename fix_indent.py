def fix_indent():
    with open("Digital_Assistant.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    start_idx = -1
    end_idx = -1
    for i, l in enumerate(lines):
        if l.startswith("if any(exit_phrase in query"):
            start_idx = i
        if l.startswith("def main(mode):"):
            end_idx = i - 2
            break
            
    for i in range(start_idx, end_idx):
        if lines[i].strip() == "continue" or lines[i].strip().startswith("continue "):
            lines[i] = "    return False\n"
        elif lines[i].strip() != "":
            lines[i] = "    " + lines[i]

    with open("Digital_Assistant.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
        
fix_indent()
print("Fixed indentation and syntaxes.")
