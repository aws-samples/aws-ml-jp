import os
input_dir = os.environ.get('SM_CHANNEL_TRAINING')
input_txt_path = os.path.join(input_dir,os.listdir(input_dir)[0])
with open(input_txt_path,'rt') as f:
    input_text_lines = f.read()
for input_text_line in input_text_lines.split('\n'):
    print(eval(input_text_line))
exit()