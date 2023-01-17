import re

def replace_string(text):
    # Replace ##S with [size=17][b]S[/b][/size]
    text = re.sub(r"##(.*)", r"[size=17][b]\1[/b][/size]", text)
    # Replace #S with [size=20][b]S[/b][/size]
    text = re.sub(r"#(.*)", r"[size=20][b]\1[/b][/size]", text)
    
    # Replace ```string``` with [code]string[/code]
    text = re.sub(r"```(.*?)```", r"[code]\1[/code]", text, flags=re.DOTALL)
    
    # Replace `S` with [color=red]S[/color]
    text = re.sub(r"`(.*?)`", r"[color=red]\1[/color]", text)
    return text

file_name = 'test.txt'
new_file_name = 'new_test.txt'
with open(file_name, 'r',encoding="utf-8") as f:
    text = f.read()

with open(new_file_name, 'w',encoding="utf-8") as f:
    f.write(replace_string(text))
