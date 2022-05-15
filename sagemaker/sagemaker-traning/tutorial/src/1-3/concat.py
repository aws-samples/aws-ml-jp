import os, json
channels = os.environ.get('SM_CHANNELS')
model_dir = os.environ.get('SM_MODEL_DIR')
channels_list = json.loads(channels)
output_txt = ''
for channel in channels_list:
    input_dir = os.environ.get('SM_CHANNEL_' + channel.upper())
    for file_name in sorted(os.listdir(input_dir)):
        input_txt_path = os.path.join(input_dir,file_name)
        with open(input_txt_path,'rt') as f:
            output_txt += f.read()+'\n'
with open(os.path.join(model_dir,'output.csv'),'wt') as f:
    f.write(output_txt)
print('processing completed')
exit()