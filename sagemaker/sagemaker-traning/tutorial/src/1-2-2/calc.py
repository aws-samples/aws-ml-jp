import os
input_dir = os.environ.get('SM_CHANNEL_TRAINING')
for file_name in sorted(os.listdir(input_dir)):
    input_txt_path = os.path.join(input_dir,file_name)
    with open(input_txt_path,'rt') as f:
        input_text_lines = f.read()
    for input_text_line in input_text_lines.split('\n'):
        print(eval(input_text_line))
exit()